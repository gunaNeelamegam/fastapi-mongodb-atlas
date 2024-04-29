from functools import partial, wraps
from typing import Callable
from utils.logger import log

def error_handler(func: Callable = None ,message: str = ""):
    console = log() 
    if func is None:
        return partial(error_handler , message = message)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            return response
        except Exception as e:
            console.print(e.args, message)
            return False
    return wrapper


from inspect import iscoroutinefunction
import asyncio
from threading import Thread
# async pydantic validation
callback_function = lambda result: result
def async_validation(func):
    result = []
    @wraps(func)
    def callback(*args, **kwargs):
        if iscoroutinefunction(func):
            def inner_callback(result: list):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = asyncio.run(func(*args ,**kwargs))
                print("RESULT : ", response)
                result.append(response)
            
            thread = Thread(target= inner_callback, args= [result])
            thread.daemon = True
            thread.start()
            thread.join(10)
            return result[0] if len(result) else None
         
    return callback