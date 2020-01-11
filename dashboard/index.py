import flask
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from google.cloud import bigquery
from wordcloud import WordCloud
import base64


# Create instances of a flask web framework 
server = flask.Flask(__name__)


# Dash uses the Flask web framework
# For the Dash deployment, we need to access the Flask application instance  
app = dash.Dash(
    __name__,
    server=server,
    routes_pathname_prefix="/dash/"
)


# Create Dictionary to store all Words extracted from the articles
listOfAllWords = []
# Create Dictionary to store all Authors
listOfAllAuthors = {}
# Create Dictionary to store all Tags
listOfTopTags = {}


# Use the authentication credentials to log in to the Google Cloud
client = bigquery.Client.from_service_account_json("DEFINE-YOUR-CONNECTION")


### BEGIN CREATE WORD CLOUDS ###
# Selects the corresponding words from the BigQUery table
query_words = ("SELECT Word FROM `project.dataset.table` LIMIT 100")
query_job = client.query(query_words)
query_job.result()

for row in query_job:
    listOfAllWords.append(row.Word)

# collections=False: get rid of words that are frequently grouped together
cloud = WordCloud(collocations=False, background_color="White", colormap="plasma", max_words=10, width=450, height=250).generate(str(listOfAllWords))
cloud.to_file("img/top10.png")

cloud = WordCloud(collocations=False, background_color="White", colormap="Greens", max_words=100, width=450, height=250).generate(str(listOfAllWords))
cloud.to_file("img/top100.png")

# Encode the images for HTML view 
image_logo = "img/dash-logo-new.png"  # replace with your own image
encoded_image_logo = base64.b64encode(open(image_logo, "rb").read())

image_top10 = "img/top10.png"  # replace with your own image
encoded_image_top10 = base64.b64encode(open(image_top10, "rb").read())

image_top100 = "img/top100.png"  # replace with your own image
encoded_image_top100 = base64.b64encode(open(image_top100, "rb").read())
### END CREATE WORD CLOUDS ###


### BEGIN GET ALL AUTHORS ###
# Selects the corresponding authors from the BigQUery table
query_authors = ("""SELECT Distinct(Author) FROM `project.dataset.table`
                    Order By Author""")

query_job = client.query(query_authors)
query_job.result()

listOfAllAuthors["ALL"] = "ALL"

for row in query_job:
    listOfAllAuthors[row.Author] = row.Author
### END GET ALL AUTHORS ###    


### BEGIN GET TOP TAGS ###
# Selects the corresponding Tags from the BigQUery table
query_tags = ("""SELECT distinct(TS.Tag)
                    FROM `project.dataset.table` AS AM
                    inner join `project.dataset.table` AS TS on AM.ID = TS.ID
                    Order by TS.Tag""")

query_job = client.query(query_tags)
query_job.result()

for row in query_job:
    listOfTopTags[row.Tag] = row.Tag
### END GET TOP TAGS ###


### BEGIN APP LAYOUT ###
# App Layout describes how the app will look like
app.layout = html.Div(
    children=[
        # Error Message
        html.Div(id="error-message"),
        # Top Banner
        html.Div(
            className="study-browser-banner row",
            children=[
                html.H2(className="h2-title", children="Towards Data Science Explorer"),
                html.Div(
                    className="div-logo",
                    children=html.Img(
                        className="logo", src="data:image/png;base64,{}".format(encoded_image_logo.decode())
                    ),
                ),
            ],
        ),
        # Body of the App
        html.Div(
            className="row app-body",
            children=[
                # User Controls
                html.Div(
                    className="four columns card",
                    children=[
                        # Create a dropdown component for "Top Words (Articles)" 
                        # and embed the resulting images in HTML                            
                        html.Div(
                            className="bg-white user-control",
                            children=[
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Top Words (Articles)"),
                                            dcc.Dropdown(id="dropdown_topwords",
                                                         options=
                                                         [
                                                          {"label": "TOP 10", "value": "TOP10"},
                                                          {"label": "TOP 100", "value": "TOP100"},
                                                          ],
                                                          value="TOP10",
                                                          clearable=False
                                                        ),
                                                          html.Div(id="dropdown_topwords_output")                                               
                                    ],
                                ),
                            ],
                        ),    
                        # Create a dropdown component for "Authors" 
                        # and dynamically link the result to the "Top Article(s) from..." authors section         
                        html.Div(
                            className="bg-white user-control",
                            children=[
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Authors"),
                                            dcc.Dropdown(id="dropdown_topauthors",
                                                          options=[{"label": k, "value": k} for k in listOfAllAuthors.keys()],
                                                          value=list(listOfAllAuthors.keys())[0],
                                                          clearable=False
                                                        ),
                                    ],
                                ),
                            ],
                        )    
                    ],                  
                ),                                
                # Create a bubble chart, which visualizes the "Trends in the Data Science (Tags)"
                html.Div(
                    className="eight columns card-left",
                    children=[
                        html.Div(
                            className="bg-white",
                            children=[
                               html.H5("Trends in the Data Science (Tags)"),
                               dcc.Dropdown(id="dropdown_toptags",
                                            options=[{"label": k, "value": k} for k in listOfTopTags.keys()],
                                            value="",
                                            placeholder="Select a Tag...",
                                            multi=True,
                                            clearable=False,
                                            searchable=False
                                            ),                               
                               dcc.Graph(id="plot_tags"),
                            ],
                        ),
                        html.Div(
                            className="bg-white",
                            children=[
                               html.H5(id="dropdown_topauthors_output"),
                               dcc.Graph(id="plot_authors"),
                            ],
                        )    
                    ],
                ),
                # The memory store reverts to the default on every page refresh
                dcc.Store(id="error", storage_type="memory"),
            ],
        ),
    ]
)
### END APP LAYOUT ###


### BEGIN DEFINE APP INTERACTIVITY ###
# @app.callback: describes the interactivity of the application

# Get Top Words Images
@app.callback(
    dash.dependencies.Output("dropdown_topwords_output", "children"),
    [dash.dependencies.Input("dropdown_topwords", "value")])
def update_output_words(value):
    if (value == "TOP10"):
        return html.Img(src="data:image/png;base64,{}".format(encoded_image_top10.decode()))
    else:
        return html.Img(src="data:image/png;base64,{}".format(encoded_image_top100.decode()))


# Get the selected "Top Author"
@app.callback(
    dash.dependencies.Output("dropdown_topauthors_output", "children"),
    [dash.dependencies.Input("dropdown_topauthors", "value")])
def update_output_authors(author_value):
    return html.Div("Top Article(s) from {}".format(author_value))


# Creates bar chart for "Top Article(s) from..."
@app.callback(
    dash.dependencies.Output("plot_authors", "figure"),
    [dash.dependencies.Input("dropdown_topauthors", "value")])
def update_output_top_article(value):
    if (value == "ALL"):
        """ GET TOP 10 Articles of selected Author"""
        query_authors = ("""SELECT Title, Author, Claps, No_Responses AS Responses, Reading_time AS ReadingTime, PublishingDate AS Date, ROW_NUMBER() OVER (ORDER BY Claps desc) As Id FROM `project.dataset.table`
                           Order By Claps desc LIMIT 10
                         """)
    else:
        """ GET TOP 10 Articles of selected Author"""
        query_authors = ("""SELECT Title, Author, Claps, No_Responses AS Responses, Reading_time AS ReadingTime, PublishingDate AS Date, ROW_NUMBER() OVER (ORDER BY Claps desc) As Id FROM `project.dataset.table`
                            Where Author = "%s"
                           Order By Claps desc LIMIT 10
                         """ % (value))        

    
    df = ( client.query(query_authors).result().to_dataframe() )   

    figure = px.bar(df, x="Id", 
                    y="Claps", 
                    height=350,
                    hover_data=["Title", "Author", "Responses", "ReadingTime", "Date"],
                    labels={"Id":"Article"},
                    )
    # Customize aspect
    figure.update_traces(marker_color="rgb(53, 88, 118)")
    figure.update_layout(title={
                                "text": "Contributions ordered by Claps",
                                "y":0.9,
                                "x":0.5,
                                "xanchor": "center",
                                "yanchor": "top"},
                         plot_bgcolor = "rgb(255, 255, 255)",
                         paper_bgcolor= "rgb(255, 255, 255)"
                        )    
    figure.update_xaxes(showgrid=True, gridwidth=1, range=[1, 10], gridcolor="rgb(238, 238, 238)", zerolinecolor="rgb(238, 238, 238)") 
    figure.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgb(238, 238, 238)", zerolinecolor="rgb(238, 238, 238)")
    

    return figure



# Creates bubble chart for "Trends in the Data Science (Tags)"
@app.callback(
    dash.dependencies.Output("plot_tags", "figure"),
    [dash.dependencies.Input("dropdown_toptags", "value")])
def update_output(value):
    if (value != ""):
        value = '","'.join(value)
        
    if (value == "ALL" or value == ""):
        """ GET TOP 10 Tags by Year"""
        query_authors = ("""SELECT count(TS.Tag) AS Number, CONCAT(CAST(EXTRACT(YEAR from AM.PublishingDate) as string), "-" ,  LPAD(CAST(EXTRACT(MONTH from AM.PublishingDate) as string),2,"0") )  AS YearMonth, TS.Tag AS Tag 
                        FROM `project.dataset.table` AS AM
                        inner join `project.dataset.table` AS TS on AM.ID = TS.ID
                        Group By TS.Tag, YearMonth
                        Order by YearMonth, Number desc
                        """)
    else:
        """ GET TOP 10 Tags by Year"""
        query_authors = ("""SELECT count(TS.Tag) AS Number, CONCAT(CAST(EXTRACT(YEAR from AM.PublishingDate) as string), "-" ,  LPAD(CAST(EXTRACT(MONTH from AM.PublishingDate) as string),2,"0") )  AS YearMonth, TS.Tag AS Tag 
                        FROM `project.dataset.table` AS AM
                        inner join `project.dataset.table` AS TS on AM.ID = TS.ID
                        WHERE Tag IN ("%s")
                        Group By TS.Tag, YearMonth
                        Order by YearMonth, Number desc
                        """ % (value))     
        
    
    df = ( client.query(query_authors).result().to_dataframe() )

        
    figure = px.scatter(
                    df, 
                    y="Number", 
                    x="YearMonth",
                    size ="Number",
                    #orientation="h",
                    color="Tag",
                    hover_data=["Tag"],
                    labels={"YearMonth":"Month/Year","Number":"Frequency of Tag"},
                    height=300,
        )
    # Customize layout
    figure.update_layout(title={
                                "text": "Frequency of Tags used over the years",
                                "y":0.9,
                                "x":0.5,
                                "xanchor": "center",
                                "yanchor": "top"},
                         plot_bgcolor = "rgb(255, 255, 255)",
                         paper_bgcolor= "rgb(255, 255, 255)",
                         showlegend=True,
                         #barmode="stack"
                        )

    figure.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgb(238, 238, 238)", linecolor="rgb(238, 238, 238)") 
    figure.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgb(238, 238, 238)")        
    
    
    return figure
### END DEFINE APP INTERACTIVITY ###


#Run Dash on a Public IP
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int("8080"), debug=False)
