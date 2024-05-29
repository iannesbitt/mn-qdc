import uuid
import hashlib
import datetime
from pathlib import Path
import json

from d1_client.mnclient_2_0 import *
from d1_common.types import dataoneTypes
from d1_common.resource_map import createSimpleResourceMap

from logging import getLogger
from logging.config import dictConfig
MOD_LOC = Path(__file__).parent.absolute()
LOGCONFIG = MOD_LOC.joinpath('log/config.json')
with open(LOGCONFIG, 'r') as lc:
    LOGGING_CONFIG = json.load(lc)
dictConfig(LOGGING_CONFIG)

try:
    from .defs import fmts
except:
    fmts = {'.xls': 'application/vnd.ms-excel','.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.doc': 'application/msword','.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.ppt': 'application/vnd.ms-powerpoint','.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation','.pdf': 'application/pdf','.txt': 'text/plain','.zip': 'application/zip','.ttl': 'text/turtle','.md': 'text/markdown','.rmd': 'text/x-rmarkdown','.csv': 'text/csv','.bmp': 'image/bmp','.gif': 'image/gif','.jpg': 'image/jpeg','.jpeg': 'image/jpeg','.jp2': 'image/jp2','.png': 'image/png','.tif': 'image/geotiff','.svg': 'image/svg+xml','.nc': 'netCDF-4','.py': 'application/x-python','.hdf': 'application/x-hdf','.hdf5': 'application/x-hdf5','.tab': 'text/plain','.gz': 'application/x-gzip','.html': 'text/html','.htm': 'text/html','.xml': 'text/xml','.ps': 'application/postscript','.tsv': 'text/tsv','.rtf': 'application/rtf','.mp4': 'video/mp4','.r': 'application/R','.rar': 'application/x-rar-compressed','.fasta': 'application/x-fasta','.fastq': 'application/x-fasta','.fas': 'application/x-fasta',}

split_str = '<qdc:qualifieddc '
rpt_txt = """
Package creation report:
Failed uploads:     %s
Successful uploads: %s

Failed packages:
%s

Successful packages:
%s
"""

def get_token():
    """
    Paste your auth token into '.d1_token'
    """
    # Set the D1 token
    with open('.d1_token', 'r') as tf:
        return tf.read().split('\n')[0]


def get_orcid():
    """
    Paste your orcid into '.orcid'
    """
    # Set your ORCID
    with open('.orcid', 'r') as orf:
        return orf.read().split('\n')[0]


def get_mn():
    """
    Put member node config into '.mn_config' in the format:

        urn:node:SI;https://smithsonian.dataone.org/metacat/d1/mn/
    """
    # set the mn url
    with open('.mn_config', 'r') as mcf:
        return mcf.read().split('\n')[0].split(';')


def parse_qdc_file():
    """
    """
    with open('qdc.xml', 'r') as f:
        qdcb = f.read()
        qdcs = qdcb.split('<wrapper>')[1].split('</wrapper>')[0].split(f'\n{split_str}')
    return qdcs


def generate_sys_meta(pid: str, sid: str, format_id: str, size: int, md5, now, orcid: str):
    """
    Fills out the system metadata object with the needed properties
    :param pid: The pid of the system metadata document
    :param format_id: The format of the document being described
    :param size: The size of the document that is being described
    :param md5: The md5 hash of the document being described
    :param now: The current time
    :param orcid: The uploader's orcid
    """
    # create sysmeta and fill out relevant fields
    sys_meta = dataoneTypes.systemMetadata()
    sys_meta.identifier = str(pid)
    sys_meta.seriesId = sid
    sys_meta.formatId = format_id
    sys_meta.size = size
    sys_meta.rightsHolder = orcid
    # calculate checksums, set dates, and set public access
    sys_meta.checksum = dataoneTypes.checksum(str(md5))
    sys_meta.checksum.algorithm = 'MD5'
    sys_meta.dateUploaded = now
    sys_meta.dateSysMetadataModified = now
    sys_meta.accessPolicy = generate_public_access_policy()
    return sys_meta


def generate_system_metadata(pid: str, sid: str, format_id: str, science_object: bytes, orcid: str):
    """
    Generates a system metadata document.
    :param pid: The pid that the object will have
    :param format_id: The format of the object (e.g text/csv)
    :param science_object: The object that is being described
    :return:
    """
    # Check that the science_object is unicode, attempt to convert it if it's a str
    if not isinstance(science_object, bytes):
        if isinstance(science_object, str):
            science_object = science_object.encode("utf-8")
        else:
            raise ValueError('Supplied science_object is not unicode')
    size = len(science_object)
    md5 = hashlib.md5()
    md5.update(science_object)
    md5 = md5.hexdigest()
    now = datetime.datetime.now()
    sys_meta = generate_sys_meta(pid, sid, format_id, size, md5, now, orcid)
    return sys_meta


def generate_public_access_policy():
    """
    Creates the access policy for the object. Note that the permission is set to 'read'.
    """
    accessPolicy = dataoneTypes.accessPolicy()
    accessRule = dataoneTypes.AccessRule()
    accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
    permission = dataoneTypes.Permission('read')
    accessRule.permission.append(permission)
    accessPolicy.append(accessRule)
    return accessPolicy


def get_format(fmt: Path):
    """
    """
    L = getLogger(__name__)
    if fmt.suffix:
        format_id = fmts.get(fmt.suffix.lower())
        if format_id:
            L.debug(f'Found format id {format_id}')
            return format_id
    L.debug(f'No format id could be found. Using "application/octet-stream"')
    return "application/octet-stream"


def create_package(orcid: str, doi: str, qdc_bytes: str, client: MemberNodeClient_2_0):
    """
    """
    L = getLogger(__name__)
    # Create and upload the EML
    qdc_pid = str(uuid.uuid4())
    meta_sm = generate_system_metadata(pid=qdc_pid,
                                       sid=doi,
                                       format_id='http://ns.dataone.org/metadata/schema/onedcx/v1.0',
                                       science_object=qdc_bytes,
                                       orcid=orcid)
    rmd = client.create(qdc_pid, qdc_bytes, meta_sm)
    L.debug(f'{doi} Received response for metadata object upload:\n{rmd}')
    # Get and upload the data
    doidir = Path(doi)
    files = []
    if doidir.exists():
        files = doidir.glob('*')
    else:
        raise FileNotFoundError(f'No directory found at {doidir}')
    # keep track of data pids for resource mapping
    data_pids = []
    for f in files:
        fformat = get_format(f)
        data_pid = str(uuid.uuid4())
        data_pids.append(data_pid)
        data_bytes = f.read_bytes()
        data_sm = generate_system_metadata(pid=data_pid,
                                           sid=doi,
                                           format_id=fformat,
                                           science_object=data_bytes,
                                           orcid=orcid)
        dmd = client.create(data_pid, data_bytes, data_sm)
        L.debug(f'{doi} Received response for science object upload:\n{dmd}')
    # Create and upload the resource map
    ore_pid = str(uuid.uuid4())
    ore = createSimpleResourceMap(ore_pid, qdc_pid, data_pids)
    ore_meta = generate_system_metadata(pid=ore_pid,
                                        sid=doi,
                                        format_id='http://www.openarchives.org/ore/terms',
                                        science_object=ore.serialize(),
                                        orcid=orcid)
    mmd = client.create(ore_pid, ore.serialize(), ore_meta)
    L.debug(f'{doi} Received response for resource map upload:\n{mmd}')
    return qdc_pid


def report(succ: int, fail: int, finished_dois: list, failed_dois: list):
    """
    """
    L = getLogger(__name__)
    finished_str = "\n".join(str(x) for x in finished_dois)
    failed_str = "\n".join(str(x) for x in failed_dois)
    L.info(rpt_txt % (fail, succ, failed_str, finished_str))


def create_packages(qdcs: list, orcid: str, client: MemberNodeClient_2_0):
    """
    Package creation and upload loop.
    """
    L = getLogger(__name__)
    n = len(qdcs)
    i = 0
    er = 0
    succ_list = []
    err_list = []
    try:
        for qdc in qdcs:
            i += 1
            qdc = f'{split_str}{qdc}'
            doi = qdc.split('<dc:identifier>')[1].split('</dc:identifier>')[0]
            L.info(f'({i}/{n}) Working on {doi}')
            try:
                qdc_pid = create_package(orcid, doi, qdc, client)
                L.info(f'{doi} done. PID: {qdc_pid}')
                succ_list.append(doi)
            except Exception as e:
                er += 1
                err_list.append(doi)
                L.error(f'{doi} / {repr(e)}: {e}')
    except KeyboardInterrupt:
        L.info('Caught KeyboardInterrupt; generating report...')
    finally:
        report(succ=i-er, fail=er, finished_dois=succ_list, failed_dois=err_list)


if __name__ == "__main__":
    """
    Set config items then start upload loop.
    """
    L = getLogger(__name__)
    # Set config items
    auth_token = get_token()
    orcid = get_orcid()
    L.info(f'Using ORCiD {orcid}')
    node, mn_url = get_mn()
    L.info(f'Using {node} at {mn_url}')
    # Set the token in the request header
    options: dict = {"headers": {"Authorization": "Bearer " + auth_token}}
    # Create the Member Node Client
    client: MemberNodeClient_2_0 = MemberNodeClient_2_0(mn_url, **options)
    qdcs = parse_qdc_file()
    L.info(f'Found {len(qdcs)} QDC objects')
    create_packages(qdcs=qdcs, orcid=orcid, client=client)