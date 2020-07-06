# from flask_back import app
from flask_back.collect.pcapParse.Control import MainCollect
if __name__ == "__main__":
    task = {
        "protocol":"HL7",
        "time":1,
        "path":"pcap"
    }
    MainCollect.put(task)
    while True:
        continue
    pass