A5='remaining_iterations'
A4='processed_urls'
A3='Processing'
A2='status'
A1='total_urls'
A0='tryPercent'
z='/app/tmpf'
y='No file uploaded'
x='file'
w='application/xml'
p='iteration_times'
o='URL'
n='domain_info'
m='cancelFlag'
l='column_data'
k='column_number'
j='row_number'
i='sheet_number'
h='selected_column'
g=isinstance
f=range
e=open
c='pInfo_obj'
b='data'
a='selected_sheet'
Z=len
Y=enumerate
W='Expiration Date'
V='Response Message'
U='Status Code'
T=False
S='error_message'
R='POST'
N=Exception
M='error'
L=True
J=str
I=None
H=print
from flask import Flask,render_template as O,request as C,jsonify as D,make_response as q,Response as r,send_from_directory as A6
import json as X
from io import StringIO as A7,BytesIO as s
import random,string,pandas as K,openpyxl as A8,logging as A,asyncio as P,pandas as K,os as E,uuid
from domain_checker import process_urls_async as d,progress_info as F
B=Flask(__name__)
A9={}
@B.route('/')
def AH():return O('url_Project.html')
@B.route('/robots.txt')
def AI():return A6('static','robots.txt')
@B.route('/set-cookie',methods=[R])
def AJ():
	K='user_id';H='cookie_consent';B=J(uuid.uuid4());A9[B]=L;I={K:B,H:C.cookies.get(H)};M='/app/storage';D=E.path.join(M,'cookie_data.json')
	if not E.path.exists(D):
		with e(D,'w')as A:X.dump([I],A,indent=4)
	else:
		with e(D,'r+')as A:
			try:F=X.load(A)
			except X.decoder.JSONDecodeError:F=[]
			F.append(I);A.seek(0);X.dump(F,A,indent=4)
	G=q();G.set_cookie(K,B,max_age=365*24*60*60);G.set_cookie(H,'true',max_age=365*24*60*60);return G
@B.route('/guide.html')
def AK():return O('guide.html')
@B.route('/favicon.ico')
def AL():return'dummy',200
@B.route('/disclaimer.html')
def AM():return O('disclaimer.html')
@B.route('/privacyPolicy.html')
def AN():return O('privacyPolicy.html')
@B.route('/templates/sitemap.xml')
def AO():A='<?xml version="1.0" encoding="UTF-8"?>\n    <urlset\n      xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n      xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n    \n    <url>\n      <loc>https://urlproject.azurewebsites.net/</loc>\n      <lastmod>2024-04-05T15:09:03+00:00</lastmod>\n      <priority>1.00</priority>\n    </url>\n    <url>\n      <loc>https://urlproject.azurewebsites.net/templates/disclaimer.html</loc>\n      <lastmod>2024-04-05T15:09:03+00:00</lastmod>\n      <priority>0.80</priority>\n    </url>\n    <url>\n      <loc>https://urlproject.azurewebsites.net/templates/privacyPolicy.html</loc>\n      <lastmod>2024-04-05T15:09:03+00:00</lastmod>\n      <priority>0.80</priority>\n    </url>\n    \n    </urlset>\n    ';return r(A,mimetype=w)
@B.route('/templates/ror.xml')
def AP():A='<?xml version="1.0" encoding="UTF-8"?>\n    <rss version="2.0" xmlns:ror="http://rorweb.com/0.1/" >\n    <channel>\n      <title>ROR Sitemap for https://urlproject.azurewebsites.net/</title>\n      <link>https://urlproject.azurewebsites.net/</link>\n    \n    <item>\n         <link>https://urlproject.azurewebsites.net/</link>\n         <title>Home Page</title>\n         <description>Home Page</description>\n         <ror:updatePeriod></ror:updatePeriod>\n         <ror:sortOrder>0</ror:sortOrder>\n         <ror:resourceOf>sitemap</ror:resourceOf>\n    </item>\n    <item>\n         <link>https://urlproject.azurewebsites.net/templates/disclaimer.html</link>\n         <title>Terms &amp; conditions</title>\n         <description>Terms &amp; conditions</description>\n         <ror:updatePeriod></ror:updatePeriod>\n         <ror:sortOrder>1</ror:sortOrder>\n         <ror:resourceOf>sitemap</ror:resourceOf>\n    </item>\n    <item>\n         <link>https://urlproject.azurewebsites.net/templates/privacyPolicy.html</link>\n         <title>Privacy Policy</title>\n         <description>Privacy Policy</description>\n         <ror:updatePeriod></ror:updatePeriod>\n         <ror:sortOrder>1</ror:sortOrder>\n         <ror:resourceOf>sitemap</ror:resourceOf>\n    </item>\n    </channel>\n    </rss>\n    ';return r(A,mimetype=w)
@B.route('/templates/sitemap.html')
def AQ():return O('sitemap.html')
@B.route('/templates/<section_name>.html')
def AR(section_name):return O(f"{section_name}.html"),200
@B.route('/input_section',methods=[R])
def AS():
	B=C.files.get(x);E=C.form.get(a);F=C.form.get(h);A=AA(B,E,F)
	if A:return D(A)
	else:return D({S:y})
@B.route('/process_manual_input',methods=[R])
def AT():
	try:A=C.get_json();F=A['manual_data'];P=A[a];E=A[h];B=F.strip().split('\n');B=[A.strip()for A in B if A.strip()];G='\n'.join([f'"{A.replace(",","")}"'for A in B]);H=K.read_csv(A7(G),header=I,names=[E]);M=[{b:A,i:1,j:B+2,k:1}for(B,A)in Y(H[E].tolist())if K.notna(A)];return D({l:M,'is_manual':L})
	except N as O:return D({S:f"Error processing manual input: {J(O)}"}),500
def AA(uploaded_file,selected_sheet,selected_column):
	e='is_csv';d='selected_file';c='sheet_columns';D=selected_sheet;C=uploaded_file;A=selected_column
	if not C:return{S:y}
	try:
		R=C.read()
		if C.filename.endswith('.csv'):M=C.filename.split('.')[0];U=K.read_csv(s(R));V=list(U.columns);A=A or V[0];F=[{b:A,i:1,j:B+2,k:1}for(B,A)in Y(U[A].tolist())if K.notna(A)];H('Current File name for CSV Test: ',M);return{c:V,l:F,a:M,d:M,e:L}
		elif C.filename.endswith('.xlsx'):
			W=A8.load_workbook(filename=s(R),data_only=L);O=W.sheetnames;X={};F=[];g=C.filename.split('.')[0];D=D or O[0]
			for(m,P)in Y(O,start=1):
				E=W[P];n=E.max_row;o=E.max_column;B=[]
				if P==D:
					for Z in f(1,o+1):
						p=E.cell(row=1,column=Z);Q=p.value
						if Q is I:Q=f"Column_{Z}"
						B.append(Q)
					if A is I:A=B[0]
					if A not in B:return{S:f"Selected column '{A}' not found in sheet '{D}'."}
					G=B.index(A)+1;F=[{b:E.cell(row=A,column=G).value,i:m,j:A,k:G}for A in f(2,n+1)if E.cell(row=A,column=G).value];A=B[G-1]
				X[P]=B
			return{d:g,'sheet_names':O,c:X,l:F,'column_titles':B,a:D,h:A,e:T}
		else:return{S:'Unsupported file format'}
	except N as q:return{S:f"Error processing file: {J(q)}"}
A.basicConfig(level=A.DEBUG)
def AB(base_filename):
	A=base_filename;B=E.path.dirname(A);C=E.path.basename(A)
	if not E.path.exists(A):return A
	D=''.join(random.choice(string.hexdigits)for A in f(8));F=f"rk-{D}-{C}";return E.path.join(B,F)
import os as E
from flask import request as C,jsonify as D
@B.route('/process_url_data',methods=[R])
async def AU():
	X='No data retrieved';S='message'
	try:
		if not C.is_json:return D({M:'Request content must be in JSON format'})
		H=C.json;Y=H.get('clientUrlSet');F=H.get(m)
		if F:return D({S:'URL processing canceled'})
		Z=P.Semaphore(8);A.info('Starting URL processing');G=[]
		async for I in d(Y['url_list'],Z,F):
			if n in I:G.append(I)
			if F:break
		A.info('URL processing completed')
		if G:
			O=K.DataFrame(G);B=O[n].apply(K.Series)
			if U in B.columns:B[U]=B[U].apply(t)
			if V in B.columns:B[V]=B[V].apply(t)
			if W in B.columns:B[W]=K.to_datetime(B[W],unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
			if not B.empty:a='rk.csv';Q=AB(a);c=z;e=E.path.join(c,Q);B.to_csv(e,index=T);f=E.path.join(E.getcwd());return D({S:'URL data processed successfully','has_downloadable_data':L,b:O.to_json(orient='records'),'csv_filename':Q,'current_directory':f})
			else:return D({M:'No domain information available to download'})
		else:A.error(X);return D({M:X})
	except N as R:A.error(f"Error processing URL data: {R}");return D({M:J(R)})
def t(arr):return', '.join(map(J,arr))
@B.route('/progress',methods=[R])
async def AV():
	A=C.json.get(m)
	if A:
		H('cancelFlag At Progress Endpoint: ',A)
		async for B in d({},{},A):0
		return D(F)
	return D(F)
@B.route('/download/<csvFilename>',methods=[R])
def AW(csvFilename):
	F=csvFilename
	try:
		G=z;A=E.path.join(G,F);H('File Path with File name: ',A);B.logger.info(f"File Path with File name: {A}")
		if E.path.exists(A):
			with e(A,'rb')as I:C=q(I.read())
			C.headers.set('Content-Type','text/csv');C.headers.set('Content-Disposition',f"attachment; filename={F}");return C
		else:return D({M:'File not found'})
	except N as K:return D({M:J(K)})
def AC(current_directory,home_directory):
	A=current_directory
	try:
		B=E.listdir(A);H('Current directory:',A);H('Home directory:',home_directory)
		for C in B:H(C)
	except OSError as D:H(f"Error: {D}")
AD=E.path.expanduser('~')
AE=E.getcwd()
AC(AE,AD)
def AX():A=C.form.get(x);B=C.form.get('batch');D=C.form.get('url-column');E=C.form.get('sheet-name');F=C.form.get('column-name');G=C.form.get('required-data');I=C.form.get('output-file-type');H(f"File type: {A}, Batch: {B}, URL column: {D}, Selected Sheet: {E}, Selected Column: {F}, Required data: {G}, Output file type: {I}");return'Form submitted successfully'
import aiohttp as u,asyncio as P,datetime as Q,logging as A,whois,time as v
from typing import List,Dict,Any,AsyncGenerator
from tqdm import tqdm
G=T
async def AF(url,session,semaphore,cancelFlag,max_retries=2):
	R='http://';E='https://';B=url;global G;G=cancelFlag
	if not B.startswith(R)and not B.startswith(E):B=E+B;K=L
	M=T;K=T;A.info(f"Received dataSet: {B}");C=0
	while C<max_retries:
		if G:break
		try:
			async with semaphore,session.get(B,timeout=8,allow_redirects=L)as D:
				O=[D.status];Q=[D.reason]
				while D.history:
					D=D.history[0];O.append(D.status);Q.append(D.reason)
					if G:break
				if M:H('HTTP prototype was successful.')
				elif K:H('HTTPS prototype was successful.')
				return O,Q
		except u.ClientError as F:
			A.error(f"Client error fetching URL status for {B}: {F}")
			if'Server disconnected'in J(F):C+=1;continue
			elif'Cannot connect to host'in J(F):C+=1;continue
			else:C+=1;continue
		except P.TimeoutError:A.error(f"Timeout error fetching URL status for {B}. Retrying...");C+=1
		except N as S:A.error(f"Error fetching URL status for {B}: {S}");C+=1
		if C==1 and B.startswith(E):B=B.replace(E,R);M=L;continue
		await P.sleep(2);A.info('Retrying...')
	A.warning(f"Exceeded maximum retries for URL: {B}");return[I],['Exceeded maximum retries']
async def AG(url,session,semaphore,cancelFlag):
	X='Response Time';T='Domain Status';S='Fresh';R='Expired';M=cancelFlag;L='Yes';F='For Sale';C=url;global G;G=M
	try:
		H(f"Processing URL: {C}");Y=Q.datetime.now();Z=P.create_task(AF(C,session,semaphore,M));E=await P.to_thread(whois.whois,C);a,b=await Z;c=Q.datetime.now();d=(c-Y).total_seconds()
		if G:return
		J=[A for A in E.expiration_date if g(A,Q.datetime)]if g(E.expiration_date,list)else[]
		for e in E.name_servers or[]:
			if any(A in e.lower()for A in['afternic','sedo','parking']):D=L;break
		else:D='No'
		if J:K=R if any(A<Q.datetime.now()for A in J)else F if D==L else S;B=max(J,default=I)
		else:B=E.expiration_date;K=R if B and(g(B,Q.datetime)and B<Q.datetime.now())else F if D==L else S if B else'NA'
		H(f"Domain Status: {K}\nExpiration Date: {B}\nFor Sale: {D}");return{o:C,U:a,V:b,T:K,W:B,F:D,X:d}
	except N as O:A.error(f"Error fetching WHOIS information for {C}: {O}");return{o:C,U:I,V:I,T:f"{O}",W:I,F:I,X:I}
async def d(urls,semaphore,cancelFlag):
	L=cancelFlag;C=urls;global G;G=L
	try:
		P=[];F[p]=[];F[c]=[]
		async with u.ClientSession()as Q:
			R=v.time()
			for(B,O)in Y(tqdm(C,desc='Processing URLs'),1):
				if G:H('Processing canceled at iteration:',B);A.info('Process canceled by user.');yield{M:'Process canceled by user'};return
				D=await AG(O,Q,semaphore,L)
				if D is not I:P.append(D)
				S=v.time()-R;E=Z(C)-B
				if E>0 or(E==0 and B==Z(C))and not G:T=B/Z(C)*100;F[A0]=T;F[A1]=Z(C);F[A2]=A3;F[A4]=B;F[A5]=E;F[p].append(S);F[c].append(D);F[c][-1][o]=O
				yield{'current_iteration':B,n:D,m:G}
	except N as K:
		if G:A.info(f"Process stopped by user: {K}")
		else:A.error(f"Error processing URLs: {K}")
		yield{M:J(K)}
F={A0:0,A4:0,A1:0,A2:A3,p:[],c:[],A5:0}
