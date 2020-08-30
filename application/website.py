import sys, os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
from bottle import route, run, static_file, request
import settings
import app
import timeit

def renderTable(tuples):
    printResult = """<style type='text/css'> h1 {color:red;} h2 {color:blue;} p {color:green;} </style>
    <table border = '1' frame = 'above'>"""

    header='<tr><th>'+'</th><th>'.join([str(x) for x in tuples[0]])+'</th></tr>'
    data='<tr>'+'</tr><tr>'.join(['<td>'+'</td><td>'.join([str(y) for y in row])+'</td>' for row in tuples[1:]])+'</tr>'
        
    printResult += header+data+"</table>"
    return printResult

@route('/classify')
def classify():
    r1 = request.query.topn or "Unknown pubid"
    table = app.classify(r1)
    return "<html><body>" + renderTable(table) + "</body></html>"
	
@route('/updateweight')
def updateweight():
    class1 = request.query.class1
    subclass = request.query.subclass
    weight = request.query.weight
    table = app.updateweight(class1,subclass,weight)
    return "<html><body>" + renderTable(table) + "</body></html>"
	
@route('/selectTopNClasses')
def selectTopNClasses():
    fromdate = request.query.fromdate
    todate = request.query.todate
    n = request.query.n
    table = app.selectTopNClasses(fromdate,todate,n)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/countArticles')
def countArticles():
    class1 = request.query.class1
    subclass = request.query.subclass
    table = app.countArticles(class1,subclass)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/findSimilarArticles')
def findSimilarArticles():
    articleId = request.query.class1
    n = request.query.n
    table = app.findSimilarArticles(articleId,n)
    return "<html><body>" + renderTable(table) + "</body></html>"


	
@route('/:path')
def callback(path):
    return static_file(path, 'web')

@route('/')
def callback():
    return static_file("index.html", 'web')

run(host='localhost', port=settings.web_port, reloader=True, debug=True)
