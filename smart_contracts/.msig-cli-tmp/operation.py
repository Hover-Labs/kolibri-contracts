
import smartpy as sp

def operation(self):
  arg = sp.unit

  transfer_operation = sp.transfer_operation(
    arg,
    sp.mutez(0), 
    sp.contract(None, sp.address("KT1JdufSdfg3WyxWJcCRNsBFV9V3x9TQBkJ2"), "pause"
  ).open_some())
  
  operation_list = [ transfer_operation ]
  
  sp.result(operation_list)

sp.add_expression_compilation_target("operation", operation)
