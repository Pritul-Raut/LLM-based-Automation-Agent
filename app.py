
# ///script
# requires-python = ">=3.13"
# dependencies = [
#     "fastapi>=0.115.8",
#     "numpy>=2.2.2",
#     "openai>=1.61.1",
#     "pandas>=2.2.3",
#     "python-dateutil>=2.9.0.post0",
#     "requests >=2.28.1",
#     "scikit-learn>=1.6.1",
#     "uvicorn>=0.34.0",
#     "sqlite3>=3.36.0",
#     "bs4>=0.0.1",
#     "pillow>=9.0.0",
#     "markdown2>=2.4.0",
#      "pydub>=0.25.1",
#     "gitpython>=3.1.24",
#      "SpeechRecognition>=3.8.1"
# ]



from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import requests
import os
import json
import subprocess
import glob
from datetime import datetime
from dateutil import parser
import base64
import mimetypes
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import html
import sqlite3
from bs4 import BeautifulSoup
import PIL
import markdown2
import git

ai_proxy_url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
ai_proxy_embeddings_url = "http://aiproxy.sanand.workers.dev/openai/v1/embeddings"
ai_proxy_api = os.environ.get("AIPROXY_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def start():
    return "You are at the entrance URL. Just write /run or /read to perform the task."

@app.get("/read")
async def read_file(path: str):
    #path=os.path.join(os.getcwd(), path)
    print(path)
    if not path:
        raise HTTPException(status_code=400, detail="File path is required")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    if not is_path_in_data_folder(path):
         return {"status": "error", "message": "File path is not in the data folder."}

    try:
        with open(path, 'r') as file:
            content = file.read()
        return PlainTextResponse(content, status_code=200)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/run")
async def run_task(task: str):
   
    
    if not task:
        raise HTTPException(status_code=400, detail="Task description is required")
    

    try:
        # Simulate task execution
        task_describe =task_describer(task)
         
        
        print(type(task_describe))
        print(task_describe)
        
        
        fun_name= eval(task_describe["name"])
        arguments_json = json.loads(task_describe["arguments"])
        print(type(arguments_json))
        print(arguments_json)
        fun_back= fun_name(**arguments_json)
        
                            
        return fun_back
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if 'Failed to create assistant' in str(e):
            raise HTTPException(status_code=400, detail="gpt-4o-mini is unable to define this task")
        
        raise HTTPException(status_code=500, detail=str(e))


def function_caller(name,arguments_json):
    return "working"
  

tools =[ {
    "type": "function",
    "function": {
        "name": "data_installation",
        "description": "if there is an to take data from github and install it in the folder then this function is used",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to clone the repository"
                },
                "github_repo_url": {
                    "type": "string",
                    "description": "GitHub repository URL"
                }
            },
            "required": [
                "path",
                "github_repo_url"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "format_markdown",
        "description": "if task description consist Format the contents of a markdown file e.g. /data/format.md using prettier@3.4.2, updating the file in-place",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the markdown file"
                }
            },
            "required": [
                "file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "count_days",
        "description": "The function reads a file e.g. (/data/dates.txt) that contains a list of dates (one per line). It counts the number of dates in the list and writes this count to a new file as e.g. (/data/dates-days.txt).",
        "parameters": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "Name of the day to count"
                },
                "input_file_path": {
                    "type": "string",
                    "description": "Path to the input file containing dates"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write the count"
                }
            },
            "required": [
                "day",
                "input_file_path",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "sort_contacts",
        "description": "This function Sort the array of contacts in a file e.g.(/data/contacts.json) by last_name, then first_name, and write the result to the file path e.g. ( /data/contacts-sorted.json)",
        "parameters": {
            "type": "object",
            "properties": {
                "input_file_path": {
                    "type": "string",
                    "description": "Path to the input file containing contacts"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write sorted contacts"
                }
            },
            "required": [
                "input_file_path",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "recents_log",
        "description": "Write the first few  lines mentioned in file into another file  e.g.(Write the first few of the  most  recent 10 .log file in /data/logs/ to /data/logs-recent.txt,) most recent first",
        "parameters": {
            "type": "object",
            "properties": {
                "log_dir": {
                    "type": "string",
                    "description": "Directory containing log files"
                },
                "write_logs_to_file": {
                    "type": "string",
                    "description": "Path to the output file to write recent logs"
                },
                "number_of_logs": {
                    "type": "string",
                    "description": "Number of recent logs to write"
                }
                
            },
            "required": [
                "log_dir",
                "write_logs_to_file",
                "number_of_logs"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "first_occur_H1_in_markdownFile",
        "description": "Find all Markdown (.md) files in a folder e.g in (/data/docs/.) For each file, extract the first occurrence of each H1 (i.e. a line starting with # ). Create an index file as e.g. (/data/docs/index.json) that maps each filename (without the /data/docs/ prefix) to its title",
        "parameters": {
            "type": "object",
            "properties": {
                "marksdown_Dir": {
                    "type": "string",
                    "description": "Directory containing markdown files"
                },
                "file_to_write_occurance": {
                    "type": "string",
                    "description": "Path to the output file to write the index"
                }
            },
            "required": [
                "marksdown_Dir",
                "file_to_write_occurance"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "sender_email_extractor",
        "description": "Extract the sender’s email address from the content file as e.g.  (/data/email.txt)  and write just the email address to another file e.g. (/data/email-sender.txt)",
        "parameters": {
            "type": "object",
            "properties": {
                "email_txt_file": {
                    "type": "string",
                    "description": "Path to the email text file"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write the email address"
                }
            },
            "required": [
                "email_txt_file",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "card_no_extractor",
        "description": "Extract the specified information in task  from the image file e.g extract card number from image path ( /data/card.png ) and write it without spaces to another file as e.g. (/data/credit-card.txt)",
        "parameters": {
            "type": "object",
            "properties": {
                "img_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write the card number"
                }
            },
            "required": [
                "img_path",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "find_most_similar_comments",
        "description": "Find the most similar things like an e.g pair of comments in the file /data/comments.txt using embeddings and write them to /data/comments-similar.txt, one per line",
        "parameters": {
            "type": "object",
            "properties": {
                "comments_filepath": {
                    "type": "string",
                    "description": "Path to the file containing comments"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write the similar comments"
                }
            },
            "required": [
                "comments_filepath",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "write_SQLite_db",
        "description": "Run a SQL query on the SQLite database file like e.g. (/data/ticket-sales.db) and write the result to file e.g. (/data/ticket-sales-gold.txt) ",
        "parameters": {
            "type": "object",
            "properties": {
                "db_path": {
                    "type": "string",
                    "description": "Path to the SQLite database file"
                },
                "db_query": {
                    "type": "string",
                    "description": "SQL query to run"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to the output file to write the result"
                }
            },
            "required": [
                "db_path",
                "db_query",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "fetch_api_data",
        "description": "Fetch data from an API and save it to a file. as e.g The API URL is e.g. https://api.example.com/data.json the output file path is e.g. /data/api-data.json",
        "parameters": {
            "type": "object",
            "properties": {
                "api_url": {
                    "type": "string",
                    "description": "API URL to fetch data from"
                },
                "file_save_path": {
                    "type": "string",
                    "description": "Path to save the fetched data"
                }
            },
            "required": [
                "api_url",
                "file_save_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "clone_git_commit",
        "description": "Clone a for git repo and make a commit. The git URL is given and store it if path is mentioned else take path as None",
        "parameters": {
            "type": "object",
            "properties": {
                "git_url": {
                    "type": "string",
                    "description": "Git repository URL"
                },
                "commit_hash": {
                    "type": "string",
                    "description": "Commit hash to checkout"
                },
                "clone_path": {
                    "type": "string",
                    "description": "Path to clone the repository"
                }
            },
            "required": [
                "git_url",
                "commit_hash",
                "clone_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "scrape_website_body",
        "description": "Extract data from (i.e. scrape) a website and save it to a file. The website URL is e.g. https://example.com and the output file path is e.g. /data/website-body.html if not then send None",
        "parameters": {
            "type": "object",
            "properties": {
                "website_url": {
                    "type": "string",
                    "description": "Website URL to scrape"
                },
                "save_path": {
                    "type": "string",
                    "description": "Path to save the scraped data"
                }
            },
            "required": [
                "website_url",
                "save_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "compress_resize_img",
        "description": "Compress or resize an image or both resize and compress the image",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task to perform (compress or resize) or both (compress and resize) the image"
                },
                "img_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "save_path": {
                    "type": "string",
                    "description": "Path to save the processed image"
                }
            },
            "required": [
                "task",
                "img_path",
                "save_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "transcribe_audio",
        "description": "Transcribe audio from an MP3 file",
        "parameters": {
            "type": "object",
            "properties": {
                "audio_path": {
                    "type": "string",
                    "description": "Path to the audio file"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to save the transcribed text"
                }
            },
            "required": [
                "audio_path",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "marksdown_to_html",
        "description": "Convert Markdown to HTML",
        "parameters": {
            "type": "object",
            "properties": {
                "markdown_file": {
                    "type": "string",
                    "description": "Path to the markdown file"
                },
                "output_file_path": {
                    "type": "string",
                    "description": "Path to save the HTML file"
                }
            },
            "required": [
                "markdown_file",
                "output_file_path"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "filter_csv_return_json",
        "description": "Filters a CSV file and returns JSON data",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the CSV file"
                },
                "filter_command": {
                    "type": "string",
                    "description": "Filter command to apply"
                }
            },
            "required": [
                "file_path",
                "filter_command"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
{
    "type": "function",
    "function": {
        "name": "unidentifed_task_code_generator",
        "description": "Task Description will be provide if it is possible to Generate and run Python code for a given task and handle errors if any then this function is used",
        "parameters": {
            "type": "object",
            "properties": {
                "task_name": {
                    "type": "string",
                    "description": "The name of the task on basis of which code will be generated"
                },
                "prompt_for_code_generation": {
                    "type": "string",
                    "description": "Write best prompt to generate the code with minimum errors and maximum accuracy"
                }
            },
            "required": [
                "task_name",
                "prompt_for_code_generation"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}
# ,
# {
#     "type": "function",
#     "function": {
#         "name": "unidentifed_task",
#         "description": "if the task is not matches with any of the one then or to get any general purpose information  it will return the code to run the task",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "task_name": {
#                     "type": "string",
#                     "description": "Describe the task here"
#                 }
#             },
#             "required": [
#                 "task_name"
#             ],
#             "additionalProperties": False
#         },
#         "strict": True
#     }
# }

]


def task_describer(task):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_proxy_api}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system","content": """I will get the task description and you will match the task with the description and return the function name and arguments to be passed to the function also remember that whenever any system path is taken either input , output , file, folder add ./  before the path and be careful your work is only to give which function is suitable don't answer the question yourself of any general purpose thing
                      choose the appropriate  function which can match more than 70 percent of context and if it doesn't  match then try to give this function with highest matching context.
                      and don't make to try extra link or url  if it doesn't contains any url if only broken url is given then make it correct.
                      use only that function which has clear refernce for that similar function and don't use any function which is not related to the task and if not match then you can use unidentified_code generator function ."""}, 
                     {"role": "user","content": task}],
        "tools": tools
    }

    response = requests.post(ai_proxy_url, json=payload, headers=headers)
    
    print(response.json())
    
    if response.status_code == 200:
        response_json = response.json()  # Parse the response as JSON
        suitable_function = response_json['choices'][0]['message']['tool_calls'][0]['function']
        
        print("RESPONSE_code::" , type(suitable_function))
        return suitable_function
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to create assistant")



def is_path_in_data_folder(input_path: str):
    
    # Ensure the base directory is /data
    base_dir = os.path.abspath("./data")
    # Get the absolute path of the file
    abs_file_path = os.path.abspath(input_path)

    # Check if the file path starts with the base directory
    if not abs_file_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Access to data outside /data is not allowed")
    return True




def data_installation(path, github_repo_url):
    try:
        result = subprocess.run(
            ["git", "clone", github_repo_url, path],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return {"status": "success", "message": "Data installed successfully.", "output": result.stdout}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to install data: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_markdown(file_path):
    if not is_path_in_data_folder(file_path):
        return {"status": "error", "message": "File path is not in the data folder."}
    try:
        result = subprocess.run(
            ["npx", "prettier@3.4.2", "--write", file_path],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return {"status": "success", "message": "File formatted successfully.", "output": result.stdout}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to format file: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def count_days(day, input_file_path, output_file_path):
    if not is_path_in_data_folder(input_file_path):
        return {"status": "error", "message": "File path is not in the data folder."}
    
    try:
        with open(input_file_path, 'r') as file:
            dates = file.readlines()
        
        # Convert the day name to a corresponding weekday number (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
        days_of_week = {
            "monday": 0, "tuesday": 1, "wednesday": 2, 
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        
        if day.lower() not in days_of_week:
            return {"status": "error", "message": "Invalid day name."}
        
        day=day.lower()
        
        day_count = 0
        for date_str in dates:
            try:
                date = parser.parse(date_str.strip())
                if date.weekday() == days_of_week[day]:
                    day_count += 1
            except ValueError:
                continue  # Skip invalid date formats
        
        with open(output_file_path, 'w') as file:
            file.write(str(day_count))
        
        return {"status": "success", "message": f"Number of {day}s: {day_count}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def sort_contacts(input_file_path, output_file_path):
    if not is_path_in_data_folder(input_file_path):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(output_file_path):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    try:
        with open(input_file_path, 'r') as file:
            contacts = json.load(file)
        
        sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))
        
        with open(output_file_path, 'w') as file:
            json.dump(sorted_contacts, file, indent=4)
        
        return {"status": "success", "message": "Contacts sorted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def recents_log(log_dir: str, write_logs_to_file: str, number_of_logs: str):
    if not os.path.isdir(log_dir):
        raise HTTPException(status_code=400, detail="Log directory does not exist")
    if not is_path_in_data_folder(log_dir):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(write_logs_to_file):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    
    try:
        num_logs = int(number_of_logs)
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        log_files.sort(key=os.path.getmtime, reverse=True)
        recent_logs = log_files[:num_logs]
        
        with open(write_logs_to_file, 'w') as output_file:
            for log_file in recent_logs:
                with open(log_file, 'r') as file:
                    first_line = file.readline().strip()
                    output_file.write(first_line + "\n")
        
        return {"status": "success", "message": "Recent logs written successfully."}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid number of logs specified")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def first_occur_H1_in_markdownFile(marksdown_Dir, file_to_write_occurance):
    if not is_path_in_data_folder(marksdown_Dir):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(file_to_write_occurance):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    try:
        md_files = glob.glob(os.path.join(marksdown_Dir, "**/*.md"), recursive=True)
        index = {}
        
        for md_file in md_files:
            with open(md_file, 'r') as file:
                for line in file:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        relative_path = os.path.relpath(md_file, marksdown_Dir)
                        index[relative_path] = title
                        break
        
        with open(file_to_write_occurance, 'w') as output_file:
            json.dump(index, output_file, indent=4)
        
        return {"status": "success", "message": "Markdown index created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def sender_email_extractor(email_txt_file, output_file_path):
    if not is_path_in_data_folder(email_txt_file):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(output_file_path):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    try:
        email_address = find_email(email_txt_file)
        if email_address:
            with open(output_file_path, 'w') as file:
                file.write(email_address)
            return {"status": "success", "message": f"Extracted email address: {email_address}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to extract email address.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def card_no_extractor(img_path, output_file_path):
    if not is_path_in_data_folder(img_path):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(output_file_path):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    try:
        card_no = cardNumber_extract(img_path,output_file_path)
        if card_no:
            with open(output_file_path, 'w') as file:
                file.write(card_no)
            return {"status": "success", "message": f"Extracted card number: {card_no}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to extract card number.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def find_most_similar_comments(comments_filepath, output_file_path):
    if not is_path_in_data_folder(comments_filepath):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(output_file_path):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    try:
        output_file.write(body)
        return {"status": "success", "message": f"Body of the website is written to {save_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def compress_resize_img(task, img_path, save_path):
    if save_path is None:
        save_path = os.path.join("/data", f"{task}_image.jpg")
    from PIL import Image
    try:
        image = Image.open(img_path)
        if task.lower() == "compress":
            image.save(save_path, quality=50)
        if task.lower() == "resize":
            image.thumbnail((128, 128))
            image.save(save_path)
        return {"status": "success", "message": f"Image {task}ed and saved to {save_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def transcribe_audio(audio_path, output_file_path):
    if output_file_path is None:
        output_file_path = os.path.join("/data", "transcribed_text.txt")
    if audio_path.startswith("http"):
        audio_path = requests.get(audio_path).content
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    import speech_recognition as sr
    try:
        r = sr.Recognizer()
        audio = AudioSegment.from_file(audio_path)
        chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)
        transcript = ""
        for chunk in chunks:
            with sr.AudioFile(chunk) as source:
                audio = r.record(source)
                try:
                    text = r.recognize_google(audio)
                    transcript += text + " "
                except sr.UnknownValueError:
                    continue
        with open(output_file_path, 'w') as output_file:
            output_file.write(transcript)
        return {"status": "success", "message": f"Transcribed text written to {output_file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def marksdown_to_html(markdown_file, output_file_path):
    if not is_path_in_data_folder(markdown_file):
        return {"status": "error", "message": "Input File path is not in the data folder."}
    if not is_path_in_data_folder(output_file_path):
        return {"status": "error", "message": "Output File path is not in the data folder."}
    import markdown2
    try:
        with open(markdown_file, 'r') as file:
            markdown = file.read()
        html = markdown2.markdown(markdown)
        with open(output_file_path, 'w') as output_file:
            output_file.write(html)
        return {"status": "success", "message": f"Markdown converted to HTML and written to {output_file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def filter_csv_return_json(file_path, filter_command):
    if not is_path_in_data_folder(file_path):
        return {"status": "error", "message": "File path is not in the data folder."}
    import pandas as pd
    try:
        df = pd.read_csv(file_path)
        if filter_command:
            filtered_df = df.query(filter_command)
            json_output = filtered_df.to_json(orient="records")
        else:
            json_output = df.to_json(orient="records")
        return json_output
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def find_email(location):
    file_path = os.getcwd() + location
    with open(file_path, 'r') as file:
        content = file.read()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_proxy_api}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": """
you will get the email just you need  extract the sender’s email address and return it as a string.
"""
            },
            {
                "role": "user",
                "content": content
            }
        ]
    }

    response = requests.post(ai_proxy_url, headers=headers, json=data)
    result = response.json()

    if "choices" not in result:
        print("Error in API response:", result)
        return None

    email_address = result["choices"][0]["message"]["content"].strip()
    output_file_path = os.path.join(os.getcwd(), "data/email-sender.txt")
    with open(output_file_path, 'w') as output_file:
        output_file.write(email_address)
    
    return email_address

def find_most_similar_comments(comments_filepath,output_file_path):
    try:
        with open(comments_filepath, 'r') as file:
            comments = file.readlines()
        
        headers = {
            "Authorization": f"Bearer {ai_proxy_api}" ,
            "Content-Type": "application/json"
             
        }

        embeddings = []
        for comment in comments:
            comment = comment.strip()
            comment = html.escape(comment)

            data = {
                "input": comment,
                "model": "text-embedding-3-small",
                "encoding_format": "float"
            }
            try:
                json_data = json.dumps(data)
            except ValueError as e:
                return f"Invalid JSON: {str(e)}"
            response = requests.post(ai_proxy_embeddings_url, headers=headers, data=json_data)
            result = response.json()
            if "data" not in result:
                print(result["data"][0]["embedding"])
                print("==================")
                return f"Error in openai API response: {result}"
            embeddings.append(result["data"][0]["embedding"])

        embeddings = np.array(embeddings, dtype=float)
        similarity_matrix = cosine_similarity(embeddings)
        np.fill_diagonal(similarity_matrix, -1)  # Ignore self-similarity

        most_similar_indices = np.unravel_index(np.argmax(similarity_matrix), similarity_matrix.shape)
        comment1 = comments[most_similar_indices[0]].strip()
        comment2 = comments[most_similar_indices[1]].strip()

        output_file_path = os.path.join(os.getcwd(), "data/comments-similar.txt")
        with open(output_file_path, 'w') as output_file:
            output_file.write(comment1 + "\n" + comment2)

        return f"Most similar comments written to {output_file_path}"
    except Exception as e:
        return f"Error: {str(e)}"

def write_SQLite_db(db_path, db_query, output_file_path):
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Execute the SQL query
        cursor.execute(db_query)
        results = cursor.fetchall()
        
        # Write the results to the output file
        with open(output_file_path, 'w') as output_file:
            for row in results:
                output_file.write(','.join(map(str, row)) + '\n')
        
        # Close the database connection
        cursor.close()
        connection.close()
        
        return {"status": "success", "message": "Query executed and results written to output file."}
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"SQLite error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def fetch_api_data(api_url: str,file_save_path:str) -> dict:
    # Send a GET request to the API
    response = requests.get(api_url)

    # Determine the content type
    content_type = response.headers.get('Content-Type')

    # Decide the file extension based on the content type
    if 'application/json' in content_type:
        file_extension = '.json'
    elif 'text/html' in content_type:
        file_extension = '.html'
    elif 'text/markdown' in content_type:
        file_extension = '.md'
    elif 'audio/' in content_type:
        file_extension = '.mp3'  # Assuming mp3 for simplicity; adjust as needed
    elif 'image/' in content_type:
        file_extension = '.png'  # Assuming png for simplicity; adjust as needed
    else:
        file_extension = ''  # Default if content type is not recognized

    # Define the output file path
    file_to_store="./data/byFetch"+file_extension

    # Save the data to the appropriate file
    if 'application/json' in content_type:
        with open(file_to_store, "w") as file:
            file.write(response.text)
    else:
        with open(file_to_store, "wb") as file:
            file.write(response.content)

    # Return the JSON response
    return {
        "file_saved": file_to_store,
        "status": "Data saved successfully"
    }

def cardNumber_extract(image_path,output_file_path):
    # Read and encode the image in base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Determine the MIME type of the image
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # Default to JPEG if MIME type cannot be determined

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_proxy_api}"
    }

    data = {
        "model": "gpt-4o-mini",  # Ensure using GPT-4o (vision-capable)
        "messages": [{ 
             "role":"user",
            "content":[
                {
                    "type": "text",
                    # Let's modify the prompt to give the LLM some creativity
                     "text": "The Image contain multiple numbers at various places in image will you extract the longest number about 12-18 digits long and tell me what is that number? just tell me the number only"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "detail": "auto",
                        # Instead of passing the image URL, we create a base64 encoded data URL
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                }
            ]
        
    }]
    }

    response = requests.post(ai_proxy_url, headers=headers, json=data)

    # Handle errors
    if response.status_code == 200:
        card_no_got= response.json()["choices"][0]["message"]["content"]
        with open(output_file_path, 'w') as output_file:
            output_file.write(card_no_got)
        return card_no_got

    else:
        return f"Error: {response.status_code} - {response.text}"

def scrape_website_body(website_url: str, save_path: str ) -> str:
    try:
        # Send a GET request to the website
        response = requests.get(website_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the body content
        body_content = str(soup)

        # Use default save path if None is provided
        if "None" in save_path:
            save_path = "./data/website-body.html"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save the body content to the specified file
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(body_content)

        return f"Data saved to {save_path}"
    except requests.RequestException as e:
        return f"Failed to fetch the website content: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

def clone_git_commit(git_url: str, commit_hash: str , clone_path: str ) -> str:
    try:
        # Use default clone path if None is provided
        if clone_path is None:
            clone_path = "./cloned_repo"

        # Check if the directory exists
        original_clone_path = clone_path
        suffix = 1
        while os.path.exists(clone_path) and os.listdir(clone_path):
            clone_path = f"{original_clone_path}_{suffix}"
            suffix += 1

        # Clone the git repository
        repo = git.Repo.clone_from(git_url, clone_path)

        # Check if commit_hash is provided
        if commit_hash:
            # Checkout the specified commit
            repo.git.checkout(commit_hash)
        else:
            return "No commit hash provided. Repository cloned, but no commit was checked out."

        # Make a new commit (example: add a dummy file and commit it)
        new_file_path = os.path.join(clone_path, "dummy.txt")
        with open(new_file_path, "w") as new_file:
            new_file.write("This is a dummy file for commit.")

        repo.index.add([new_file_path])
        repo.index.commit("Added dummy file.")

        return f"Repository cloned to {clone_path} and committed a dummy file."
    except Exception as e:
        return f"Github repo is saved But failed to commit An error occurred: {e}"



def unidentifed_task(task_name):
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_proxy_api}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": """check the task and if you can solve that task or give information about that or tell me how can you achieve that task if not then just say this Right now, I am unable to do that, as I am not programmed yet to perform this task. """

            },
            {
                "role": "user",
                "content": task_name
            }
        ]
    }

    response = requests.post(ai_proxy_url, headers=headers, json=data)
    try:
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        return f"An error occurred: {e}"



def unidentifed_task_code_generator(task_name, prompt_for_code_generation):
    file_path = f"./data/{task_name}.py"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_proxy_api}"  # Ensure AI_PROXY_API is set as an environment variable
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": """
You are an coding assitant and you have to generate a code for the given task. and resolve the errors also if any. and only give me formatted of python don't give me fenced code block.remeber don't give me any comments in the code.and never give me code which can has security issues and privacy issues.and or if any code that has files write or read that path must be in ./data folder  other than this folder path is not allowed.
always give main function in which it conssit output as that the code is run succecfully and completed your task and little bit task description  otherwise it should show it has error in the code.
"""
            },
            {
                "role": "user",
                "content": prompt_for_code_generation
            }
        ]
    }

    response = requests.post(ai_proxy_url, headers=headers, json=data)
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    with open(file_path, 'w') as file:
        file.write(content)
    output,error= python_code_runner(file_path)
    
    if error is not None:
        return f"Error while completing task: {error}"

    return output
    

def python_code_runner(file_path):
    process = subprocess.Popen(["python", file_path], stdout=subprocess.PIPE)
    output, error = process.communicate()
    return output, error

    
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

