import io
import re
import getpass
import argparse
import requests
import pandas as pd
from tqdm.autonotebook import tqdm


def login(edd_url='edd.jbei.org',user=getpass.getuser()):
    '''Log in to the Electronic Data Depot (EDD).'''
    session = requests.session()
    auth_url = 'https://' + edd_url + '/accounts/login/'
    csrf_response = session.get(auth_url)
    csrf_response.raise_for_status()
    csrf_token = csrf_response.cookies['csrftoken']
    
    login_headers = {
        'Host': 'edd.jbei.org',
        'Referer': auth_url,
    }

    login_payload = {
        'csrfmiddlewaretoken': csrf_token,
        'login': user,
        'password': getpass.getpass(prompt=f'Password for {user}: '),
    }

    login_response = session.post(auth_url, data=login_payload, headers=login_headers)
    
    #Don't leave passwords laying around
    del login_payload
    
    if 'Login failed.' in login_response.text:
        print('Login Failed!')
        return None

    return session


def export_study(client,slug,edd_server='edd.jbei.org',verbose=True):
    '''Export a Study from EDD as a pandas dataframe'''
    lookup_response = client.get(f'https://{edd_server}/rest/studies/?slug={slug}')
    study_id = lookup_response.json()["results"][0]["pk"]
    
    #Get Total Number of Data Points
    export_response = client.get(f'https://{edd_server}/rest/export/?study_id={study_id}')
    data_points = int(export_response.headers.get('X-Total-Count'))
    
    #Download Data Points
    export_response = client.get(f'https://{edd_server}/rest/stream-export/?study_id={study_id}', stream=True)
        
    if export_response.encoding is None:
        export_response.encoding = 'utf-8'
    
    df = pd.DataFrame()
    count = 0
    
    export_iter = export_response.iter_lines(decode_unicode=True)
    first_line = next(export_iter)
    
    buffer = io.StringIO()
    buffer.write(first_line)
    buffer.write("\n")
    
    with tqdm(total=data_points) as pbar:
        for line in export_iter:
            if line:
                count += 1
                pbar.update(1)
                buffer.write(line)
                buffer.write("\n")
                if 0 == (count % 10000):
                    #print(f"Downloaded {count} records")
                    buffer.seek(0)
                    frame = pd.read_csv(buffer)
                    df = df.append(frame, ignore_index=True)
                    buffer.close()
                    buffer = io.StringIO()
                    buffer.write(first_line)
                    buffer.write("\n")
        buffer.seek(0)
        frame = pd.read_csv(buffer)
        df = df.append(frame, ignore_index=True)
    return df


def commandline_export():
    parser = argparse.ArgumentParser(description="Download an Study CSV from an EDD Instance")

    #Slug (Required)
    parser.add_argument("slug", help="The EDD instance study slug to download.")

    #UserName (Optional) [Defaults to Computer User Name]
    parser.add_argument('--username', help='Username for login to EDD instance.',default=getpass.getuser())

    #EDD Server (Optional) [Defaults to edd.jbei.org]
    parser.add_argument('--server', help='EDD instance server',default='edd.jbei.org')

    args = parser.parse_args()

    #Login to EDD
    session = login(edd_url=args.server,user=args.username)

    if session is not None:
        #Download Study to Dataframe
        df = export_study(session,args.slug)

        #Write to CSV
        df.to_csv(f'{args.slug}.csv')