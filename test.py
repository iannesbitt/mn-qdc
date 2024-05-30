from .run import get_config, get_token, get_format,\
    getLogger, DATA_ROOT, MemberNodeClient_2_0,\
    parse_qdc_file, split_str, Path, report


def testpaths(doi: str):
    """
    Test directory structure for a given DOI. If no dir is found, then decrease
    the version at the end of the DOI until a directory is found that matches.
    """
    L = getLogger(__name__)
    doidir = Path(DATA_ROOT / doi)
    flist = []
    if doidir.exists():
        for f in doidir.glob('*'):
            flist.append(f)
    else:
        # we need to figure out where the closest version is (or if it exists?)
        try:
            [doiroot, version] = doidir.stem.split('.v')
            version = int(version)
            versions = 0
            L.info(f'{doi} found version {version}')
            while True:
                version -= 1
                moddir = Path(DATA_ROOT / f'{doiroot}.v{version}')
                L.debug(f'Trying {moddir}')
                if moddir.exists():
                    versions += 1
                    fi = 0
                    for f in moddir.glob('*'):
                        flist.append(f)
                        fi += 1
                    L.info(f'Found {fi} existing files in version {version} directory')
                    if version > 0:
                        L.info('Looking for previous versions...')
                        continue
                    else:
                        L.info(f'Found {versions} versions of doi root {doiroot}')
                        break
        except ValueError:
            L.info(f'{doi} has no version.')
        except Exception as e:
            L.error(f'{repr(e)} has occurred: {e}')
    return flist


def testdata(qdcs: list):
    """
    Parse the QDC record and start the directory testing function.
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
            if not qdc:
                continue
            qdc = f'{split_str}{qdc}'
            L.debug(f'QDC:\n{qdc}')
            doi = qdc.split('<dc:identifier>')[1].split('</dc:identifier>')[0]
            L.info(f'({i}/{n}) Working on {doi}')
            try:
                qdc_files = testpaths(doi)
                if len(qdc_files) > 0:
                    L.info(f'{doi} done. Files:\n{qdc_files}')
                    succ_list.append(doi)
                else:
                    L.info(f'No files found for {doi}')
                    err_list.append(doi)
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
    Set config items then start test loop.
    """
    L = getLogger(__name__)
    # Set config items
    auth_token = get_token()
    orcid, node, mn_url = get_config()
    L.info(f'Rightsholder ORCiD {orcid}')
    L.info(f'Using {node} at {mn_url}')
    L.info(f'Root path: {DATA_ROOT}')
    # Set the token in the request header
    options: dict = {"headers": {"Authorization": "Bearer " + auth_token}}
    # Create the Member Node Client
    client: MemberNodeClient_2_0 = MemberNodeClient_2_0(mn_url, **options)
    qdcs = parse_qdc_file()
    L.info(f'Found {len(qdcs)} QDC records')
    testdata(qdcs=qdcs)
    client._session.close()
