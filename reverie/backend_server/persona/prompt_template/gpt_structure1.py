"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs, with optional Ollama backend.
"""
import json
import random
import openai
import time
import urllib.request

from utils import *

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
# Set LLM_BACKEND = "openai"  to use OpenAI (default).
# Set LLM_BACKEND = "ollama"  to use Ollama (local or cloud).
#
# When using Ollama the client is still the openai-python library but pointed
# at the Ollama base URL, which exposes an OpenAI-compatible /v1 endpoint.
# ---------------------------------------------------------------------------

_backend = globals().get("LLM_BACKEND", "openai").lower()

if _backend == "ollama":
  _ollama_base = globals().get("ollama_base_url", "https://ollama.com/")
  _ollama_api_key = globals().get("ollama_api_key", "ollama")
  _client = openai.OpenAI(
    base_url=f"{_ollama_base.rstrip('/')}/v1",
    api_key=_ollama_api_key,
  )
  # Model aliases: map the GPT model names used in this file to Ollama models.
  _CHAT_MODEL   = globals().get("ollama_chat_model",      "llama3")
  _GPT4_MODEL   = globals().get("ollama_gpt4_model",      "llama3")
  _EMBED_MODEL  = globals().get("ollama_embedding_model", "nomic-embed-text")
else:
  _openai_key = globals().get("openai_api_key", "")
  openai.api_key = _openai_key
  _client = openai.OpenAI(api_key=_openai_key)
  _CHAT_MODEL  = "gpt-3.5-turbo"
  _GPT4_MODEL  = "gpt-4"
  _EMBED_MODEL = "text-embedding-ada-002"


def _chat_complete(model, messages):
  """Thin wrapper: calls the configured backend's chat completion endpoint."""
  completion = _client.chat.completions.create(model=model, messages=messages)
  return completion.choices[0].message.content


def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def ChatGPT_single_request(prompt):
  temp_sleep()
  return _chat_complete(_CHAT_MODEL, [{"role": "user", "content": prompt}])


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt):
  """
  Given a prompt, make a request to the configured LLM backend and return
  the response string.
  """
  temp_sleep()

  try:
    return _chat_complete(_GPT4_MODEL, [{"role": "user", "content": prompt}])
  except:
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def ChatGPT_request(prompt):
  """
  Given a prompt, make a request to the configured LLM backend and return
  the response string.
  """
  try:
    return _chat_complete(_CHAT_MODEL, [{"role": "user", "content": prompt}])
  except:
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def GPT4_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = GPT4_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response_OLD(prompt, 
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass
  print ("FAIL SAFE TRIGGERED") 
  return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt, gpt_parameter):
  """
  Given a prompt and a dictionary of GPT parameters, make a request to the
  configured LLM backend and return the response string.

  When using the Ollama backend the legacy text-completion API is unavailable,
  so the prompt is forwarded as a chat message to the chat model instead.
  """
  temp_sleep()
  try:
    if _backend == "ollama":
      # Ollama has no legacy /v1/completions endpoint; use chat completions.
      return _chat_complete(_CHAT_MODEL, [{"role": "user", "content": prompt}])
    else:
      response = _client.completions.create(
                  model=gpt_parameter["engine"],
                  prompt=prompt,
                  temperature=gpt_parameter["temperature"],
                  max_tokens=gpt_parameter["max_tokens"],
                  top_p=gpt_parameter["top_p"],
                  frequency_penalty=gpt_parameter["frequency_penalty"],
                  presence_penalty=gpt_parameter["presence_penalty"],
                  stream=gpt_parameter["stream"],
                  stop=gpt_parameter["stop"])
      return response.choices[0].text
  except:
    print ("TOKEN LIMIT EXCEEDED")
    return "TOKEN LIMIT EXCEEDED"


def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print (prompt)

  for i in range(repeat): 
    curr_gpt_response = GPT_request(prompt, gpt_parameter)
    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  return fail_safe_response


def get_embedding(text, model=None):
  text = text.replace("\n", " ")
  if not text:
    text = "this is blank"
  if model is None:
    model = _EMBED_MODEL
  response = _client.embeddings.create(input=[text], model=model)
  return response.data[0].embedding


if __name__ == '__main__':
  gpt_parameter = {"engine": "text-davinci-003", "max_tokens": 50, 
                   "temperature": 0, "top_p": 1, "stream": False,
                   "frequency_penalty": 0, "presence_penalty": 0, 
                   "stop": ['"']}
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response): 
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(gpt_response):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)




















