# BootRAG
A RAG self built by LLMs

After seeing the succes of the DeepSeek model since it was introduced, I wanted to have a go at getting an LLM to write a real application with minimum programmed input from a human. I chose a RAG because that's something that will help move it forward as it develops itself.

Although I am a programmer, when I started I knew very little about python or RAGS or any of the modules that the llm has generated code for, I didn't choose them or know their APIs.

To get the code up and running I decided on python as the backend, interfacing to the Llama.cpp web interface. It has an html front end. The idea is to bootstrap using the python code until I can drop the llama.cpp html interface and rely soley on my own code. My long term goal is to have a flexible middle layer that can cater for a variety of apps

Everything here has been 99% written by a small number of models but the great majority has been the Deepseek models. I'm usng various DeepSeek blends of the 14B parameter models as they just about run comfortably on my dev machine. There are a few cases where I have made changes, mainly because the speed of code generation would mean I have to wait 20 minutes to fix one line but I do let the generation run to confirm that my change was picked up by the LLM.

The idea is to use minimal dependancies in the end. The vector database is a simple sqlite3 database at the moment. The similarity code is a simple cosine difference

At the moment it can accept text or file input and store chunks in an sqlite database but they are not yet passed through to the backend for use.

It can accept a query and generate a response which is displayed in it's own response div, although the developer recently broke the code and now the response divs overwrite each other.

Feel free to contribute but not with code. Please submit prompts along with the model you used to generate the code. The code doesn't have to be generated perfectly, I will make small fixes or adapt the prompt for the models I use.

Once cloned, the app can be run by changeing to the Bootstrap directory and running python api.py

I am using a python virtual environment and  the python packages I needed to install on my machine were:

flask
sklearn
scikit-learn
torch
langchain_community
sentence-transformers
llama-cpp-python

I will generate a requirements.txt soon.

