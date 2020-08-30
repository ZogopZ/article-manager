# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import sys, os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import pymysql as db
import settings


def connection():
    ''' User this function to create your connections '''
    con = db.connect(
        settings.mysql_host, 
        settings.mysql_user, 
        settings.mysql_passwd, 
        settings.mysql_schema)
    
    return con


def classify(topn):
   
    con=connection() # Create a new connection
    cur=con.cursor() # Create a cursor on the connection
    
    nonClassifiedArticlesQuery = ('SELECT title, summary '
                                  'FROM articles '
                                  'WHERE articles.id NOT IN (SELECT articles_id '
                                                            'FROM article_has_class) ')

    cur.execute(nonClassifiedArticlesQuery) # Execute query to find all specified rows.
    nonClassifiedTuple = cur.fetchall()  # Create a tuple with all ids and summaries of non classified articles.

    returnTuple = ()
    resultsTuple = ()
    for title, text in nonClassifiedTuple:
        summary = ''.join(text) # Remove unwanted characters: )(,'  from summary to create a string.
        wordList = summary.split() # List all words in summary using space as a delimeter.
        statement = '' # Initialize string statement to be used with the sql query for each summary found.
        for word in wordList:
            statement = statement + '\'' + word + '\', ' # Append 'word', to statement string. This creates a string to be used with the sql query below.
        statement = statement.rstrip(', ') # Remove last comma and space from statement in order to succefully execute the sql query.
        resultsQuery = ('SELECT class, subclass, SUM(weight) AS weight_sum '
                        'FROM classes '
                        'WHERE classes.term IN (%s) '
                        'GROUP BY class, subclass '
                        'ORDER BY weight_sum DESC ' %statement)
        cur.execute(resultsQuery) # Execute query to find all specified rows.
        resultsTuple = cur.fetchmany(int(topn)) # Create a tuple with topN classes fetched for each non classified article.
        for result in resultsTuple: 
            # For each result fetched, add the title of the non classified article and convert float weight to string,
            # to create a tuple which contains all needed information to be returned.
            returnTuple = returnTuple + tuple([[title] + [result[0]] + [result[1]] + [str(result[2])]])
    returnList = list(returnTuple) # Convert tuple to list, to be used with the return statement.
    
    return [("title","class","subclass", "weightsum"),] + returnList


def updateweight(class1, subclass, weight):
        
    con=connection() # Create a new connection
    cur=con.cursor() # Create a cursor on the connection

    weightsQuery = ('SELECT term, weight '
                    'FROM classes '
                    'WHERE class = \'%s\' AND subclass = \'%s\' AND weight > %s ' %(class1, subclass, weight))
    cur.execute(weightsQuery) # Execute query to find specified rows.
    weightTuple = cur.fetchall() # Fetch all weights greater than weight variable, according to class1 and subclass variables.
    if len(weightTuple) == 0: # If this tuple is empty, no weights where found meeting the above criteria.
        returnList = [("error",),]
    else:
        weightList = list(weightTuple) # Convert tuple to list, to update weights.
        for term, weightOld in weightList:
            weightOld = float(str(weightOld).strip(')(,\'')) # Convert to string and then to int type and remove leading and trailing characters: )(,' 
            weightNew = weightOld - (weightOld - float(weight))/2 # Reduce weight according to given information.
            updateWeightsQuery = ('UPDATE classes '
                                  'SET weight = %s '
                                  'WHERE class = \'%s\' AND subclass = \'%s\' AND term = \'%s\' AND weight = %s ' %(str(weightNew), class1, subclass, term, weightOld))
            cur.execute(updateWeightsQuery) # Execute query to update specified weights in database.

        con.commit() # Commit changes to database.
        returnList = [("ok",),]
    
    return [("result",),] + returnList
    
	
def selectTopNClasses(fromdate, todate, n):

    con=connection() # Create a new connection
    cur=con.cursor() # Create a cursor on the connection
    
    topNClassesQuery = ('SELECT class, subclass, COUNT(articles.id) AS total_articles '
                        'FROM articles '
                        'INNER JOIN article_has_class ON articles.id = article_has_class.articles_id '
                        'WHERE date BETWEEN \'%s\' AND \'%s\' '
                        'GROUP BY class, subclass '
                        'ORDER BY total_articles DESC LIMIT %s ' %(fromdate, todate, n))
    cur.execute(topNClassesQuery) # Execute query to find top N catecories according to given dates.
    topNClassesTuple = cur.fetchall() # Create a tuple with all categories fetched.
    returnList = list(topNClassesTuple) # Convert tuple to list to be used with the return statement.
    
    return [("class","subclass", "count"),] + returnList

def countArticles(class1, subclass):

    con=connection() # Create a new connection
    cur=con.cursor() # Create a cursor on the connection
    
    countArticlesQuery = ('SELECT COUNT(articles.id) AS total_articles '
                          'FROM articles '
                          'INNER JOIN article_has_class ON articles.id = article_has_class.articles_id '
                          'WHERE class = \'%s\' AND subclass = \'%s\' ' %(class1, subclass))
    cur.execute(countArticlesQuery) # Execute query to find the sum of all articles of given category.
    countArticlesTuple = cur.fetchall() # Create a tuple with the sum fetched.
    returnList = list(countArticlesTuple) # Convert tuple to list to be used with the return statement.
    
    return [("count",),] + returnList


def findSimilarArticles(articleId, n):

    con=connection() # Create a new connection
    cur=con.cursor() # Create a cursor on the connection

    summaryQuery = ('SELECT summary '
                    'FROM articles '
                    'WHERE id = %s ' %(articleId))
    cur.execute(summaryQuery) # Execute query to find the summary of the article that the user specified.
    summaryTuple = cur.fetchall() # Create a tuple with the summary fetched.
    originalSummary = ''.join(summaryTuple[0]) # Convert tuple to string to be used with jSimilarity function.
    summariesQuery = ('SELECT id, summary '
                      'FROM articles '
                      'WHERE NOT id = %s ' %(articleId))
    cur.execute(summariesQuery) # Execute query to find all other ids and summaries.
    summariesTuple = cur.fetchall() # Create a tuple with all ids and summaries fetched.
    resultsList = [] # Create a list to store ids and jaccardi similarity of each article compared to user specified article.
    for articleId1, summary in summariesTuple:
        summaryToCheck = str(summary) # Convert tuple to string to be used with findJSimilarity function.
        jSimilarity = findJSimilarity(originalSummary, summaryToCheck) # Find Jaccardi similarity of these two summaries.
        resultsList.append((jSimilarity, articleId1)) # Append values to list.
    resultsList.sort() # Sort list by Jaccardi similarity. Lowest values will be first. 
    
    tempN = int(n) 
    returnList = []
    for jSimilarity, id in reversed(resultsList): # Reversed because greatest Jaccardi similarities will be at the end of the list.
        if tempN == 0:
            break
        returnList.append([id]) # Append articles ids to the returnList.
        tempN = tempN - 1 # For loop will repeat tempN or n times and will get the needed results.
    
    return [("articleid",),] + returnList

def findJSimilarity(string1, string2): # Function to calculate Jaccardi Similarity between two strings.

    A = set(string1.split()) # Create a set of all the words of user specified article's summary.
    B = set(string2.split()) # Create a set of all the words of another article's summary.
    C = A.intersection(B) # Get the common words of sets A and B. (common words of the two summaries)
    jSimilarity = float(len(C)/len(A)+len(B)-len(C)) # Calculate Jaccardi similarity. (A ∩ B/A ∪ B) or (C/A ∪ B)

    return jSimilarity