from enum import Enum
class CallFunction():
    function_name: str
    call_sequence: int
    # 0-interrupt generation
    # 1-before generation;2-after generation;
    # 3-after user reply
    # 4-before banching;5-after banching.
    call_position: int = 0
    # 0-do nothing
    # 1-data fill and inner task
    # 2-receive data from the previous function
    request_process: int = 0
    # 0-do nothing
    # 1-data backfill
    # 2-send data to the next function
    response_process: int = 0
    copy_conv: bool = False
    use_template_prompt: bool = True
    system: str
    task: str

    def __init__(self,
                 function_name:str,
                 call_sequence:int,
                 call_position:int,
                 request_process:int,
                 response_process:int,
                 copy_conv:bool,
                 use_template_prompt:bool,
                 system:str,
                 task:str
                 ) -> None:
        self.function_name = function_name
        self.call_sequence = call_sequence
        self.call_position = call_position
        self.request_process = request_process
        self.response_process = response_process
        self.copy_conv = copy_conv
        self.use_template_prompt = use_template_prompt
        self.system = system
        self.task = task  


class Function_Enum(Enum):
    WEBCRAWLER = "WEBCRAWLER"
    INNERCALL = "INNERCALL"
    SHELL = "SHELL"
    CLIENTRUNSHELL = "CLIENTRUNSHELL"
    STANDARDHTTP = "STANDARDHTTP"
    LOCALLIB = "LOCALLIB"
    GETTIME = "GETTIME"
    ENCRYPT = "ENCRYPT"
    DECRYPT = "DECRYPT"
    LOADDIALOGUE = "LOADDIALOGUE"
    SAVEDIALOGUR = "SAVEDIALOGUE"