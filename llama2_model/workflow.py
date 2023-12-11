import os
import json
from typing import List
from llama2_model.conversation import Conversation,SeparatorStyle

class WorkFlowConv(Conversation):
    flow_name: str
    task: str
    flow_id: int
    front_flow_id: List[int] = []
    copy_conv: bool = True
    replied: bool = False
    class next_flow:
        # condition_type: 0-automatic;1-manual;2-linear
        condition_type: int = 2
        condition_system: str 
        condition: str
        linear_next_id: int
        branch: dict
        def __init__(self,
                     condition_type:int,
                     condition_system:str,
                     condition:str,
                     linear_next_id:int,
                     branch:dict):
                self.condition_type = condition_type
                self.condition_system = condition_system
                self.condition = condition
                self.linear_next_id = linear_next_id
                self.branch = branch
            
    def __init__(self,
                 system:str,
                 roles:List[str],
                 messages:List[List[str]],
                 task:str,
                 flow_id:int,
                 copy_conv:int,
                 next_flow:next_flow):
        self.system = system
        self.roles = roles
        self.messages = messages
        self.offset = 2
        self.sep_style = SeparatorStyle.TRI
        self.sep = "<|im_start|>"
        self.sep2 = "<|im_end|>"
        self.sep3 = "</s>"
        self.task = task
        self.flow_id = flow_id
        self.copy_conv = copy_conv
        self.next_flow = next_flow
        
    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()
    
class FlowChat():

    def __init__(self) -> None:
        pass
    
    def custom_decoder(self,d):
        inner = WorkFlowConv.next_flow(condition_type=d["next_flow"]["condition_type"],
                                       condition_system=d["next_flow"]["condition_system"],
                                       condition=d["next_flow"]["condition"],
                                       linear_next_id=d["next_flow"]["linear_next_id"],
                                       branch=d["next_flow"]["branch"])
        return WorkFlowConv(system=d["system"],roles=d["roles"],messages=d["messages"],
                            task=d["task"],flow_id=d["flow_id"],copy_conv=d["copy_conv"],
                            next_flow=inner)

    def get_workflow(self):
        workflow_dir = './work_dir'
        flow_list = []
        for item in os.scandir(workflow_dir):
            if item.is_dir():
                flow_list.append(item.path)
        print(flow_list)
        return flow_list

    def get_flow_node(self,flow_name,node_id):
        flow_node_file = flow_name+'/node'+str(node_id)+'.json'
        with open(flow_node_file,'r',encoding='utf-8') as f:
            data = f.read()
        return data

    def init_senario(self,senario):
        jsonData = self.get_flow_node(flow_name = senario,node_id = 0)
        d = json.loads(jsonData.strip('\t\r\n'))
        woflco = self.custom_decoder(d = d)
        woflco.flow_name = senario
        return woflco

    def get_front_node(self,workflow:WorkFlowConv):
        if len(workflow.front_flow_id) == 0:
            print('reach the head node')
            return workflow
        front_node_id = workflow.front_flow_id.pop()
        if front_node_id == workflow.flow_id:
            return workflow
        jsonData = self.get_flow_node(flow_name=workflow.flow_name,node_id=front_node_id)
        d = json.loads(jsonData.strip())
        woflco = self.custom_decoder(d = d)
        woflco.front_flow_id = workflow.front_flow_id
        woflco.flow_name = workflow.flow_name
        return woflco

    def get_next_node(self,workflow:WorkFlowConv,next_id):
        if next_id == -1:
            workflow.flow_id = -1
            print('workflow ends')
            return workflow 
        if next_id == workflow.flow_id:
            workflow.front_flow_id.append(workflow.flow_id)
            return workflow
        jsonData = self.get_flow_node(flow_name=workflow.flow_name,node_id=next_id)
        d = json.loads(jsonData.strip('\t\r\n'))
        woflco = self.custom_decoder(d = d)
        woflco.front_flow_id.append(workflow.flow_id)
        woflco.flow_name = workflow.flow_name
        return woflco
    
    def condition_check(self,workflow:WorkFlowConv,output_text):
        if  len(workflow.next_flow.branch) != 0:
            for check in workflow.next_flow.branch:
                if output_text.find(check) != -1:
                    next_id  = workflow.next_flow.branch.get(check)
                    workflow = self.get_next_node(workflow=workflow,next_id=next_id)
                    return workflow
            print("can not find branch!")
            workflow.replied = False
        return workflow
        