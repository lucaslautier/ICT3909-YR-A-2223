import gensim
import pandas as pd
import subprocess

from flask import Flask, redirect, url_for, render_template, request

def loadModel():

    lda_model = gensim.models.ldamodel.LdaModel.load("ldaModel_maltese/lda_model.model")

    x=lda_model.show_topics(num_topics=10, num_words=500,formatted=False)
    topics_words = [(tp[0], [wd[0] for wd in tp[1]]) for tp in x]

    print(x[0])
    print(topics_words[3])

    #Below Code Prints Topics and Words
    fields = ["Topic", "Word", "Frequency"]

    topicNum = []
    words = []
    frequency  =[]

    i= 0
    formattedData = []
    for i in x:
        for j in i[1]:
            topicNum.append(i[0])
            words.append(j[0])
            frequency.append(j[1])

    formattedData = {'Topic': topicNum, 'Word': words, 'Frequency': frequency}
    ldaDF = pd.DataFrame(formattedData)
    ldaDF.to_csv('LDAModel_10.csv', encoding="utf-8")

    return ldaDF, topics_words

#format to get one word from topic words
# print(topics_words[3][1])

def topicFreq(input_string, ldaDF):
    # filter the rows based on the search string in the "word" column
    # input_string = 'sitwazzjoni'    # THIS WILL BE WORD USER ENTERS

    wordFilter_df = ldaDF[ldaDF['Word'].str.contains(input_string)]
    wordFilter_df


    data = wordFilter_df[['Topic', 'Frequency']].values.tolist()
    print(data)

    max_frequency = 0
    max_topic = ''

    # iterate over the 2d list and update the variables if a larger number is found
    for topic, frequency in data:
        if frequency > max_frequency:
            max_frequency = frequency
            max_topic = topic

    max_topic = int(max_topic)
    print(max_topic)

    return max_topic
    #print(topics_words[max_topic][1])

def ipa(input_string, topics_words, max_topic):
    # G2P of input word
    # Put word into input file
    with open('findIPA.txt', 'w', encoding="utf-8") as file:
        file.write(input_string)

    # Run .exe to get IPA format
    subprocess.run('app/MalteseG2P.exe "findIPA.txt"')

    # Read output file and store IPA format of input word
    with open('findIPA.g2p.txt', 'r', encoding="utf-8") as file:
        inputWord_IPA = file.readline()

    print(inputWord_IPA)

    # G2P of all words in the same topic as input
    toCheck_IPA = []
    lastThird = []
    # Remove duplicate words
    unique_topicWords = list(set(topics_words[max_topic][1]))

    # Put all the full strings into file (checking purposes)
    with open('fullWords.txt', 'w', encoding="utf-8") as file:
        for string in unique_topicWords:
            file.write(string + '\n')

    # Put final 1/3 of string into input file
    with open('findIPA.txt', 'w', encoding="utf-8") as file:
        for string in unique_topicWords:
            string = string[int(len(string)*2/3):]
            file.write(string + '\n')
            lastThird.append(string)

    # Run .exe to get IPA format
    subprocess.run('app/MalteseG2P.exe "findIPA.txt"')

    with open('findIPA.g2p.txt', 'r', encoding="utf-8") as file:
        for wordIPA in file:
            toCheck_IPA.append(wordIPA.strip())

    print(toCheck_IPA)

    ipaCol = ["Word", "Last Third", "IPA"]

    ipaData = {'Word': unique_topicWords,'Last Third': lastThird, 'IPA': toCheck_IPA}
    ipaDF = pd.DataFrame(ipaData)

    return ipaDF

def getRhymingWords(input_string, ipaDF):
    # Filter to get DF with input word, extract IPA
    inputWord_df = ipaDF[ipaDF['Word'] == input_string]
    input_ipaValue = inputWord_df.iloc[0]['IPA']
    print(input_ipaValue)

    #Filter original DF to only show words with same ending IPA
    mask = (ipaDF['IPA'].str.endswith(input_ipaValue)) & (ipaDF['Word'] != input_string)
    sameIPA_df = ipaDF[mask]

    rhyming_words = sameIPA_df['Word'].tolist()
    print(input_string)
    return rhyming_words

# def getPostDataAsJson(environ):
#     post_json = {}
#     storage = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

#     for k in storage.keys():
#         post_json[k] = storage.getvalue(k)

#     return (post_json)

# input_string = "sitwazzjoni"
def runner(input_string):
    # get dataframe with the LDA Frequencies
    ldaDF, topics_words = loadModel()

    

    # Find the most probable topics for the input word
    max_topic = topicFreq(input_string, ldaDF)

    # get IPA of input string and all words in most probable topic
    ipaDF = ipa(input_string, topics_words, max_topic)

    rhyming_words = getRhymingWords(input_string, ipaDF)

    return rhyming_words
    # print(rhyming_words)
# runner(input_string)
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/",methods=["POST"])
def getvalue():
    name = request.form['name']
    words = runner(name)
    print(words)
    return render_template('index.html',toRhyme = name, rhymes = words)

if __name__ == '__main__':
    app.run(debug=True)
