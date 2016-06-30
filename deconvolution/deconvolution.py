from ctypes import *

deconvdll = windll.LoadLibrary("./deconvolution/deconvolution.dll")

def deconvolution(inp_str):
    try:
        inp_bytes = inp_str.encode("utf-8")
        inp_length = len(inp_bytes)
        out_length = 10*inp_length
        out_bytes = create_string_buffer(out_length)
        error = create_string_buffer(256)
        deconvdll.solve(c_char_p(inp_bytes), c_ulong(inp_length), out_bytes, c_ulong(out_length), error)
        if error.value!=b'':
            out_bytes = error.value
            out_str = out_bytes.decode("utf-8")
            raise Exception(out_str)
        out_bytes = out_bytes.value
        out_str = out_bytes.decode("utf-8")
    except Exception as err:
        out_str = "Error: " + str(err)
    finally:
        return out_str
