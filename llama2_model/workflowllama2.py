import copy
import torch
import transformers

from threading import Thread
from transformers import TextIteratorStreamer,StoppingCriteriaList,StoppingCriteria
from llama2_model.workflow import FlowChat,WorkFlowConv
from llama2_model.conversation import Conversation

class StoppingCriteriaSub(StoppingCriteria):

    def __init__(self, stops=[], encounters=1):
        super().__init__()
        self.stops = stops

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> bool:
        for stop in self.stops:
            if torch.all(input_ids[:, -len(stop):] == stop).item():
                return True

        return False
    
class WorkflowLLAMA2:
    def __init__(self, model,tokenizer, device='cuda:0', stopping_criteria=None):
        self.device = device
        self.model = model
        self.tokenizer = tokenizer
        if stopping_criteria is None:
            stop_words_ids = [[32001],[32002], [32001,32002]]
            stop_words_ids = [torch.tensor(ids).to(device=device) for ids in stop_words_ids]
            self.stopping_criterias = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])
        else:
            self.stopping_criteria = stopping_criteria


    def answer_prepare(self,conv:Conversation, max_new_tokens=512, num_beams=1, min_length=1, top_p=0.9,
                       repetition_penalty=1.05, length_penalty=1, temperature=0.6, max_length=2000):
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        input_ids = self.tokenizer(prompt, return_tensors='pt').input_ids
        current_max_len = input_ids.shape[1] + max_new_tokens
        if current_max_len - max_length > 0:
            print('Warning: The number of tokens in current conversation exceeds the max length. '
                  'The model will not see the contexts outside the range.')
        begin_idx = max(0, current_max_len - max_length)
        input_ids = input_ids[:, begin_idx:]
        input_ids = input_ids.to(self.device)

        generation_kwargs = dict(
            {"input_ids":input_ids},
            max_new_tokens=max_new_tokens,
            stopping_criteria=self.stopping_criteria,
            num_beams=num_beams,
            do_sample=True,
            min_length=min_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            temperature=float(temperature),
        )
        return generation_kwargs

    def answer(self,
               conv:Conversation,
               **kargs):
        generation_dict = self.answer_prepare(conv, **kargs)

        output_token = self.model_generate(**generation_dict)[0]
        output_text = self.tokenizer.decode(output_token,skip_special_tokens=True)
        # get orca output
        output_text = output_text.split(conv.sep)[-1].strip()
        # try to get final answer
        if output_text.find('inal answer') != -1:
            output_text = output_text.split('inal answer')[-1].strip()
        conv.messages[-1][1] = output_text
        return output_text, output_token.cpu().numpy()

    def stream_answer(self,
                      conv:Conversation,
                      **kargs):
        generation_kwargs = self.answer_prepare(conv,  **kargs)
        streamer = TextIteratorStreamer(self.tokenizer,skip_prompt=True,skip_special_tokens=True)
        generation_kwargs['streamer'] = streamer
        thread = Thread(target=self.model_generate, kwargs=generation_kwargs)
        thread.start()
        return streamer
    
    def workflow_stream_answer(self,
                               conv:Conversation,
                               workflow:WorkFlowConv,
                               flow_name,
                               **kargs):
        flowChat = FlowChat()
        workflow = self.workflow_prepare(conv,workflow,flow_name,flowChat)
        if workflow.flow_id == -1:
            print('workflow ends')
            return None, workflow    
        conv.append_message(workflow.roles[1], None)
        if workflow.replied == False:
            workflow.replied = True
            # before generation
            # self.call_function_by_position(workflow = workflow, position = 0)
            return self.stream_answer(workflow, **kargs),workflow
        # after user reply
        # self.call_function_by_position(workflow = workflow,position = 3)
        if workflow.next_flow.condition_type == 1:
            # manual node
            # pop conv.append_message(workflow.roles[1], None)
            conv.messages.pop()
            # get user choice
            user_choice = conv.messages[-1][1]
            next_flow_id = workflow.next_flow.branch[user_choice]
            workflow = flowChat.get_next_node(workflow,next_flow_id)
            return self.workflow_stream_answer(conv, workflow, flow_name, **kargs)[0],workflow
        if workflow.next_flow.condition_type == 2:
            # linear node
            # pop conv.append_message(workflow.roles[1], None)
            conv.messages.pop()
            workflow = flowChat.get_next_node(workflow,workflow.next_flow.linear_next_id)
            return self.workflow_stream_answer(conv, workflow, flow_name, **kargs)[0],workflow
        # before branching
        # self.call_function_by_position(workflow = workflow, position = 4)
        # automatic node
        return self.answer_check(conv,flowChat,workflow, **kargs)
    
    def answer_check(self,
                     conv:Conversation,
                     flowChat:FlowChat,
                     workflow:WorkFlowConv,
                     **kargs):      
        output_text = self.answer(workflow, **kargs)[0]
        replied_flag = workflow.replied
        workflow = flowChat.condition_check(workflow=workflow,output_text=output_text)
        if replied_flag == True and workflow.flow_id != -1:
            # pop 
            conv.messages.pop()
            return self.workflow_stream_answer(conv=conv,workflow=workflow,flow_name=workflow.flow_name,**kargs)[0],workflow
        if workflow.flow_id == -1:
            print('workflow ends')
            return None, workflow
        return self.stream_answer(workflow, **kargs),workflow
    
    def answer_in_stream(self, 
                         conv:Conversation, 
                         workflow:WorkFlowConv, 
                         flow_name, 
                         **kargs):
        if flow_name is None:
            return self.stream_answer(conv, **kargs),None
        else:
            return self.workflow_stream_answer(conv, workflow, flow_name, **kargs)
         
    def workflow_prepare(self,
                         conv:Conversation,
                         workflow:WorkFlowConv,
                         senario,
                         flowChat:FlowChat):
        temp = copy.deepcopy(conv)
        # workflow init
        if workflow is None :
            workflow = flowChat.init_senario(senario=senario)
        if workflow.flow_name != senario:
            print("workflow changed")
        if len(workflow.system) == 0:
            workflow.system = temp.system

        # end of workflow
        if workflow.flow_id == -1:
            return workflow
        
        # repeat current node
        if workflow.replied == True and workflow.node_repeat != 0:
            workflow.node_repeat -= 1
            workflow.replied = False

        # deal linear node and manual node
        if workflow.replied == True and workflow.next_flow.condition_type != 0 :
            return workflow
        
        # give llm a task to find next node
        if workflow.replied == True:
            workflow.messages = temp.messages
            workflow.system = workflow.next_flow.condition_system
            workflow.append_message(workflow.roles[0],workflow.next_flow.condition)
            return workflow
        
        # If this node is strongly associated with history dialogue, 
        # please set copy_conv == True
        if workflow.copy_conv == True :
            workflow.messages = temp.messages
            temp_user_reply = temp.messages.pop()
            workflow.append_message(workflow.roles[0],workflow.task)
            workflow.messages.append(temp_user_reply)
            return workflow
        
        # If this node is history dialogue indendent, 
        # please set copy_conv == False
        if workflow.copy_conv == False:
            workflow.messages = []
            temp_user_reply = temp.messages.pop()
            workflow.append_message(workflow.roles[0],workflow.task)
            workflow.messages.append(temp.messages[-1])
            workflow.messages.append(temp_user_reply)
        return workflow
            
    def call_function_by_position(self,workflow:WorkFlowConv, position:int = 0):
        function_tmp = workflow.function_list[position]
        for value in function_tmp.values():
            pass
        pass

    def model_generate(self, *args, **kwargs):
        # for 8 bit and 16 bit compatibility
        output = self.model.generate(*args, **kwargs)
        return output