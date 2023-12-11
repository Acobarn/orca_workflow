# Wolkflow Driven Orca2 Demo
 The purpose of this demo is to show how a nodalized workflow can help designers control the flow of LLM and user interactions as much as possible. 
 In this demo, the following features are demonstrated:
 1: the topic of the conversation is dominated by LLM(designer); 
 2: requests from the user are handled in the correct processing order;
 3: automatic branching of the process is performed by LLM evaluating the current node's task completion.

## How does it work
 Designer can preset the system prompt word and the node's task node by node, enabling the LLM to respond to users based on the current node's task. The designer's tasks are hidden from the user and are not added to the history dialogue.
 At each node, process branching can be customized separately, the following  methods are provided: 
 1: LLM automatic branching. Perform an additional round of reasoning, allowing AI to determine branches based on the conditions preset by the designer.It can handle scenarios where user input information is complex and unpredictable;
 2: user manual branching.Provide branch options to users, allowing users to manually select branches, with only one round of inference per conversation. It can handle scenarios scenarios where user input needs to be constrained, and scenarios where user input information is relatively simple and predictable;
 3: linear node. Forcefully enter the next node without evaluating the completion status of the current node.It can handle scenarios where non essential user information is collected and the current node task does not have a significant impact on subsequent nodes.

## How to use it
 **1. Prepare the code and the environment**
 ```bash
 git clone https://github.com/Acobarn/orca_workflow.git
 cd orca_workflow
 pip install -r ./requirements.txt
 ```
 **2. Prepare the LLM weights**
 Because of Orca2's excellent single-task reasoning ability and standardized final answer output format, I chose this model as the evaluation engine for automatic branching.
 Please download the llm weights.
 [Download](https://huggingface.co/microsoft/Orca-2-13b/tree/main)
 Place those weights in the ./orca2_weight path
 **3. Run the demo**
 ```bash
 python ./orca_demo.py
 ```
 In the Demo's 'Chose a workflow for Orca2' module,you can found the author's pre-built auto-branching example and the manual branching example. It is a simple workflow that LLM collects some infomation from user ,then give user a name for thier avatar. 
 **4. Add your own workflow**
 Those examples locate on the ./work_dir directory. You can design your own workflow node by node, following the patterns and rules of the examples. This demo supports mixing multiple branching methods in one workflow.

## What is Orca2
 Orca 2 is a finetuned version of LLAMA-2 that created by Microsoft.Orca 2 is built for research purposes only and provides a single turn response in tasks such as reasoning over user given data, reading comprehension, math problem solving and text summarization. The model is designed to excel particularly in reasoning.
 More details and paper can be viewed on Microsoft's Hunggingface repository:
 https://huggingface.co/microsoft/Orca-2-13b

## TODO
 ### call function