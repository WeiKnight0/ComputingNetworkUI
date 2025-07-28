# 这是一个关于序列化保存和反序列化恢复的示例
class Foo(object):
  def __init__(self, val=2):
     self.val = val
  def __getstate__(self):
     print("I'm being pickled")
     self.val *= 2
     return self.__dict__
  def __setstate__(self, d):
     print("I'm being unpickled with these values: " + repr(d))
     self.__dict__ = d
     self.val *= 3

import pickle
f = Foo()
f_data = pickle.dumps(f)
f_new = pickle.loads(f_data)
print(f"f_new的类型为{type(f_new)}")