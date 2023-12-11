import dataclasses
from enum import auto, Enum
from typing import List, Tuple, Any

class SeparatorStyle(Enum):
    """Different separator style."""
    SINGLE = auto()
    TWO = auto()
    TRI = auto()

@dataclasses.dataclass
class Conversation:
    system: str
    roles: List[str]
    messages: List[List[str]]
    offset: int
    sep_style: SeparatorStyle = SeparatorStyle.TRI
    sep: str = "<|im_start|>"
    sep2: str = "<|im_end|>"
    sep3: str = "</s>"

    skip_next: bool = False
    conv_id: Any = None

    def get_prompt(self):
        if self.sep_style == SeparatorStyle.SINGLE:
            ret = self.system + self.sep
            for role, message in self.messages:
                if message:
                    ret += role + message + self.sep
                else:
                    ret += role
            return ret
        elif self.sep_style == SeparatorStyle.TRI:
            seps = [self.sep,self.sep2, self.sep3]
            ret = seps[0] + 'system\n' + self.system + seps[1] + '\n'
            for i, (role, message) in enumerate(self.messages):
                if message:
                    if role != self.roles[1]:
                        sepend = seps[1]
                    else:
                        sepend = seps[2]
                    ret += seps[0] + role +'\n'+ message + sepend+ '\n' 
                else:
                    ret += seps[0] + role +'\n'
            return ret
        else:
            raise ValueError(f"Invalid style: {self.sep_style}")

    def append_message(self, role, message):
        self.messages.append([role, message])

    def to_gradio_chatbot(self):
        ret = []
        for i, (role, msg) in enumerate(self.messages[self.offset:]):
            if i % 2 == 0:
                ret.append([msg, None])
            else:
                ret[-1][-1] = msg
        return ret

    def copy(self):
        return Conversation(
            system=self.system,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            sep2=self.sep2,
            sep3=self.sep3,
            conv_id=self.conv_id)

    def dict(self):
        return {
            "system": self.system,
            "roles": self.roles,
            "messages": self.messages,
            "offset": self.offset,
            "sep": self.sep,
            "sep2": self.sep2,
            "sep3": self.sep3,
            "conv_id": self.conv_id,
        }
    
CONV_OCRA2 = Conversation(
    system="You are Orca, an AI language model created by Microsoft.",
    roles=("user", "assistant"),
    messages=[],
    offset=2,
    sep_style=SeparatorStyle.TRI,
    sep="<|im_start|>",
    sep2="<|im_end|>",
    sep3="</s>"
)