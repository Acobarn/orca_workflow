import os
import sys
import gradio as gr
import torch
import transformers
from transformers import StoppingCriteriaList
from llama2_model.conversation import CONV_OCRA2,Conversation
from llama2_model.workflowllama2 import StoppingCriteriaSub,WorkflowLLAMA2
from llama2_model.workflow import FlowChat,WorkFlowConv

if not torch.cuda.is_available():
    print("This demo does not work on CPU.")
    sys.exit()

MAX_MAX_NEW_TOKENS = 2048
DEFAULT_MAX_NEW_TOKENS = 1024
MAX_INPUT_TOKEN_LENGTH = int(os.getenv("MAX_INPUT_TOKEN_LENGTH", "4096"))

system_message = "You are Orca, an AI language model created by Microsoft. You are a cautious assistant. You carefully follow instructions. You are helpful and harmless and you follow ethical guidelines and promote positive behavior."

model_id = "./orca2_weight"

model = transformers.AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", load_in_8bit=True)
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, use_fast=False)

stop_words_ids = [[32001],[32002], [32001,32002]]
stop_words_ids = [torch.tensor(ids).to(device='cuda:0') for ids in stop_words_ids]
stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])
chat = WorkflowLLAMA2(model, tokenizer, device='cuda:0', stopping_criteria=stopping_criteria)
flowChat = FlowChat()
flow_list = flowChat.get_workflow()
DESCRIPTION = """
# Orca-2
The system message is set to be the cautious system message:
You are Orca, an AI language model created by Microsoft. You are a cautious assistant. You carefully follow instructions. You are helpful and harmless and you follow ethical guidelines and promote positive behavior.
"""

# ========================================
#             Gradio Setting
# ========================================

def gradio_reset(chat_state:Conversation):
    chat_state = CONV_OCRA2.copy()
    return chat_state,gr.update(interactive = True,value = None),gr.Radio(choices = [], interactive = False, value = None),None,None

def gradio_retry(chatbot,
                 chat_state:Conversation,
                 workflow:WorkFlowConv ):
    chatbot[-1][1] = None
    chat_state.messages.pop()
    if workflow is not None:
        workflow.replied = False
        workflow.messages = []
    return chatbot, chat_state,workflow

def gradio_undo(chatbot,
                chat_state:Conversation,
                workflow:WorkFlowConv):
    user_message:list[str] = ['','']
    if  len(chatbot) != 0:
        chatbot.pop()
    else :
        return chatbot, chat_state, None, gr.update(interactive = True, value = '')
    if len(chat_state.messages) > 1:
        chat_state.messages.pop()
        user_message = chat_state.messages.pop()
    if len(chat_state.messages) == 0 :
        chat_state.append_message(chat_state.roles[0], "")
    if workflow is not None:
       workflow =  flowChat.get_front_node(workflow)
    return chatbot, chat_state,workflow,gr.update(interactive = True,value = user_message[-1])

def gradio_change_role(user_role_input,
                       chat_state:Conversation):
    roles_temp = list(chat_state.roles)
    roles_temp[0] = user_role_input
    chat_state.roles = tuple(roles_temp)
    return chat_state

def gradio_ask(user_message,
               chatbot,
               chat_state:Conversation):
    if len(user_message) == 0:
        return gr.update(interactive=True, placeholder='Input should not be empty!'), chatbot, chat_state
    if chat_state is None:
        chat_state = CONV_OCRA2.copy()
    chat_state.append_message(chat_state.roles[0],user_message)
    chatbot = chatbot + [[chat_state.roles[0] + ': ' + user_message, None]]
    return '', chatbot, chat_state

def gradio_answer(chatbot,
                  chat_state:Conversation,
                  workflow:WorkFlowConv,
                  num_beams,
                  temperature,
                  flow_name):
    answer_kwargs = dict(
        conv = chat_state,
        num_beams = num_beams,
        temperature = temperature,
        max_new_tokens = DEFAULT_MAX_NEW_TOKENS,
        max_length = MAX_INPUT_TOKEN_LENGTH
    )
    streamer,workflow = chat.answer_in_stream(**answer_kwargs,
                                    workflow = workflow,
                                    flow_name = flow_name)
    if streamer is None:
        chatbot[-1][1] = chat_state.roles[1] + ': workflow ends. Please restart chat'
        chat_state = CONV_OCRA2.copy()
        yield chatbot, chat_state, workflow
        return chatbot, chat_state, workflow
    
    output = ''
    for new_output in streamer:
        output += new_output
        chatbot[-1][1] = chat_state.roles[1] + ': ' + output
        yield chatbot, chat_state, workflow
    chat_state.messages[-1][1] = output.split(chat_state.sep)[0]
    return chatbot, chat_state, workflow

def manual_condition(workflow:WorkFlowConv):
    if workflow is None:
        return gr.Radio(choices = [], interactive = False),gr.update(interactive = True, value = '')
    if workflow.replied and workflow.next_flow.condition_type == 1:
        flow_condition = []
        for key in workflow.next_flow.branch.keys():
            flow_condition.append(key)
        return gr.Radio(choices = flow_condition,interactive = True), gr.update(interactive = False, placeholder='Please Choice an Option!')  
    return gr.Radio(choices = [], interactive = False),gr.update(interactive = True, value = '')

title = """<h1 align="center">Demo of workflow driven Orca2</h1>"""
description = """<h3>This is a demo of workflow driven Orca2. Chose a workflow and start chatting!</h3>"""


with gr.Blocks() as demo:
    gr.Markdown(title)
    gr.Markdown(description)

    chat_state = gr.State()
    chatbot = gr.Chatbot(label = 'Orca2')
    workflow = gr.State()
    options = gr.Radio(choices = [],interactive = False)
    text_input = gr.Textbox(label = 'User',
                            placeholder = 'You can close a workflow before conv',
                            interactive = True)
    flow_name = gr.Radio(choices = flow_list,
                         label = 'Chose a workflow for Orca2',
                         info = 'Here will show the workflow dir')
    
    with gr.Row(visible = True) as userinput_col:
        retry_button = gr.Button("retry")
        undo_button = gr.Button("undo")
        clear = gr.Button("Restart")
    with gr.Row(visible = True) as userrole_col:
        user_role_input = gr.Textbox(label = 'UserRole', 
                                     placeholder = 'You can change your role during conv',
                                     interactive = True)
        change_role = gr.Button("ChangeRole")

    # Not Used         
    role_input = gr.Textbox(label = 'Orca2SystemRole', 
                            placeholder ='You can give Orca2 a system promt to improve its performance',
                            interactive = True)
    # Greedy
    num_beams = gr.Slider(
        minimum=1,
        maximum=10,
        value=1,
        step=1,
        interactive=True,
        label="beam search numbers",
    )
    # Random
    temperature = gr.Slider(
        minimum=0.1,
        maximum=2.0,
        value=0.6,
        step=0.1,
        interactive=True,
        label="Temperature",
    )
    options.change(gradio_ask, [options, chatbot, chat_state], 
                      [text_input, chatbot, chat_state]
                      ).then(
                          gradio_answer, [chatbot, chat_state,workflow, num_beams, temperature,flow_name],
                          [chatbot, chat_state, workflow]
                          ).then(
                             manual_condition,[workflow],[options,text_input] 
                          )   
    text_input.submit(gradio_ask, [text_input, chatbot, chat_state], 
                      [text_input, chatbot, chat_state]
                      ).then(
                          gradio_answer, [chatbot, chat_state,workflow, num_beams, temperature,flow_name],
                          [chatbot, chat_state, workflow]
                          ).then(
                             manual_condition,[workflow],[options,text_input] 
                          )
    retry_button.click(gradio_retry, [ chatbot, chat_state,workflow], 
                      [ chatbot, chat_state,workflow]
                      ).then(
                          gradio_answer, [chatbot, chat_state,workflow, num_beams, temperature,flow_name],
                          [chatbot, chat_state,workflow]
                          ).then(
                             manual_condition,[workflow],[options,text_input] 
                          )
    clear.click(gradio_reset, [chat_state], 
                [ chat_state,text_input,options,chatbot,workflow], queue=False
                )
    undo_button.click(
        gradio_undo,[chatbot,chat_state,workflow],
        [chatbot,chat_state,workflow,text_input]
    )
    change_role.click(gradio_change_role, [user_role_input,chat_state],[chat_state])

demo.queue(max_size=2).launch(server_name="0.0.0.0")