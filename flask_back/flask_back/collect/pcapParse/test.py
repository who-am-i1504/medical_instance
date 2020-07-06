from protocol.dcmReader import readDcm, prase
from protocol.state import dealIPPort
import dpktConstruct
import dpktHttpConstruct
import PduConstruct

if __name__=='__main__':
    
    # PduConstruct.construct('pcap/20200625', 'dicom.pcap', 'DICOM')
    # dpktHttpConstruct.construct('pcap/20200625', 'http.pcap', 'astm|hl7|dicom|HTTP', filter=True)
    dpktConstruct.construct('pcap/test', 'ftp.pcap', 'astm|hl7|dicom|FTP')
    # dpktConstruct.construct('pcap/20200625', 'astm.pcap', 'ASTM')
    # dpktConstruct.construct('pcap/20200625', 'hl7.pcap', 'HL7')



    # dealIPPort("Y_1592988297.802338_120.220.186.228-80_10.246.229.255-60332.unknow")
    # prase('pcap/test/DICOM')
    # print("DICOM generate finished.")
    # prase('pcap/test/HTTP')
    # print("HTTP generate finished.")
    # prase('pcap/test/FTP')
    # print("FTP generate finished.")
    # parse('pcap/test/DICOM')
    # parse('pcap/test/DICOM')
    # construct('E:\\29161\\Destop\\medical_instance\\pcap', 'http_download.pcap', 'http', filter=True)