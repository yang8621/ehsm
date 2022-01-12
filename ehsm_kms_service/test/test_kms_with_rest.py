import requests
import json
import argparse
import base64
import time
import random
import hmac
from hashlib import sha256
from collections import OrderedDict
import urllib.parse

appid=''
appkey = ''

def test_creat_app_info(base_url, headers):
    print('====================test_creat_app_info start===========================')
    creat_app_info_resp = requests.post(url=base_url + "RA_GET_API_KEY", data=json.dumps({}), headers=headers)
    if(check_result(creat_app_info_resp, 'RA_GET_API_KEY', 'test_creat_app_info') == False):
        return
    global appid 
    global appkey 
    appid = json.loads(creat_app_info_resp.text)['result']['appid']
    appkey = json.loads(creat_app_info_resp.text)['result']['appkey']
    print('CreateKey resp(EH_AES_GCM_128):\n%s\n' %(creat_app_info_resp.text))
    print('====================test_creat_app_info end===========================')


def test_params(payload):
    params = OrderedDict()
    params["appid"] = appid
    params["payload"] = urllib.parse.unquote(urllib.parse.urlencode(payload))
    params["timestamp"] = str(int(time.time() * 1000))
    sign_string = urllib.parse.unquote(urllib.parse.urlencode(params))
    sign = str(base64.b64encode(hmac.new(appkey.encode('utf-8'), sign_string.encode('utf-8'), digestmod=sha256).digest()),'utf-8')
    params["payload"] = payload
    params["sign"] = sign
    return params
    
def test_export_datakey(base_url, headers):
    print('====================test_export_datakey start===========================')
    params=test_params({
            "keyspec":"EH_AES_GCM_128",
            "origin":"EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_export_datakey') == False):
        return
    print('CreateKey resp(EH_AES_GCM_128):\n%s\n' %(create_resp.text))

    params=test_params({
            "keyspec":"EH_RSA_3072",
            "origin":"EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_ukey_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_ukey_resp, 'CreateKey', 'test_export_datakey') == False):
        return
    print('CreateKey resp(EH_RSA_3072):\n%s\n' %(create_ukey_resp.text))


    # test GenerateDataKeyWithoutPlaintext
    params=test_params({
            "aad": "test",
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "keylen": 48,
        })
    print('GenerateDataKeyWithoutPlaintext req:\n%s\n' %(params))
    generateDataKeyWithoutPlaintext_resp = requests.post(url=base_url + "GenerateDataKeyWithoutPlaintext", data=json.dumps(params), headers=headers)
    if(check_result(generateDataKeyWithoutPlaintext_resp, 'GenerateDataKeyWithoutPlaintext', 'test_export_datakey') == False):
        return
    print('GenerateDataKeyWithoutPlaintext resp:\n%s\n' %(generateDataKeyWithoutPlaintext_resp.text))

    # test ExportDataKey
    params=test_params({
            "aad":"test",
            "cmk_base64":json.loads(create_resp.text)['result']['cmk_base64'],
            "olddatakey_base":json.loads(generateDataKeyWithoutPlaintext_resp.text)['result']['ciphertext_base64'],
            "ukey_base64":json.loads(create_ukey_resp.text)['result']['cmk_base64'],
        })
    print('ExportDataKey req:\n%s\n' %(params))
    exportDataKey_resp = requests.post(url=base_url + "ExportDataKey", data=json.dumps(params), headers=headers)
    if(check_result(exportDataKey_resp, 'ExportDataKey', 'test_export_datakey') == False):
        return
    print('ExportDataKey resp:\n%s\n' %(exportDataKey_resp.text))

    print('====================test_export_datakey end===========================')

def test_RSA3072_encrypt_decrypt(base_url, headers):
    print('====================test_RSA3072_encrypt_decrypt start===========================')
    params=test_params({
            "keyspec":"EH_RSA_3072",
            "origin":"EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_RSA3072_encrypt_decrypt') == False):
        return
    print('CreateKey resp:\n%s\n' %(create_resp.text))

    # test AsymmetricEncrypt("123456")
    params=test_params({
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "plaintext": "123456"
        })
    print('AsymmetricEncrypt req:\n%s\n' %(params))
    asymmetricEncrypt_resp = requests.post(url=base_url + "AsymmetricEncrypt", data=json.dumps(params), headers=headers)
    if(check_result(asymmetricEncrypt_resp, 'AsymmetricEncrypt', 'test_RSA3072_encrypt_decrypt') == False):
        return
    print('AsymmetricEncrypt resp:\n%s\n' %(asymmetricEncrypt_resp.text))

    # test AsymmetricDecrypt(ciphertext)
    params=test_params({
            "ciphertext_base64": json.loads(asymmetricEncrypt_resp.text)['result']['ciphertext_base64'],
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
        })
    print('AsymmetricDecrypt req:\n%s\n' %(params))
    asymmetricDecrypt_resp = requests.post(url=base_url + "AsymmetricDecrypt", data=json.dumps(params), headers=headers)
    if(check_result(asymmetricDecrypt_resp, 'AsymmetricDecrypt', 'test_RSA3072_encrypt_decrypt') == False):
        return
    print('AsymmetricDecrypt resp:\n%s\n' %(asymmetricDecrypt_resp.text))

    plaintext = str(base64.b64decode(json.loads(asymmetricDecrypt_resp.text)['result']['plaintext_base64']), 'utf-8').strip(b"\x00".decode())
    print('AsymmetricDecrypt plaintext:\n%s\n' %(plaintext))
    print('====================test_RSA3072_encrypt_decrypt end===========================')

def test_Stest_RSA3072_sign_verify(base_url, headers):
    print('====================test_Stest_RSA3072_sign_verify start===========================')
    params=test_params({
            "keyspec": "EH_RSA_3072",
            "origin": "EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_Stest_RSA3072_sign_verify') == False):
        return
    print('CreateKey resp:\n%s\n' %(create_resp.text))

    # test Sign
    params=test_params({
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "digest": "test"
        })
    print('Sign req:\n%s\n' %(params))
    sign_resp = requests.post(url=base_url + "Sign", data=json.dumps(params), headers=headers)
    if(check_result(sign_resp, 'Sign', 'test_Stest_RSA3072_sign_verify') == False):
        return
    print('Sign resp:\n%s\n' %(sign_resp.text))

    # test Verify
    params=test_params({
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "digest": "test",
            "signature_base64": json.loads(sign_resp.text)['result']['signature_base64'],
        })
    print('Verify req:\n%s\n' %(params))
    verify_resp = requests.post(url=base_url + "Verify", data=json.dumps(params), headers=headers)
    if(check_result(verify_resp, 'Verify', 'test_Stest_RSA3072_sign_verify') == False):
        return
    print('Verify resp:\n%s\n' %(verify_resp.text))

    print('====================test_Stest_RSA3072_sign_verify end===========================')

def test_GenerateDataKeyWithoutPlaintext(base_url, headers):
    print('====================test_GenerateDataKeyWithoutPlaintext start===========================')
    params=test_params({
            "keyspec": "EH_AES_GCM_128",
            "origin": "EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_GenerateDataKeyWithoutPlaintext') == False):
        return
    print('CreateKey resp:\n%s\n' %(create_resp.text))

    # test GenerateDataKeyWithoutPlaintext
    params=test_params({
            "aad": "test",
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "keylen": 48,
        })
    print('GenerateDataKeyWithoutPlaintext req:\n%s\n' %(params))
    generateDataKeyWithoutPlaintext_resp = requests.post(url=base_url + "GenerateDataKeyWithoutPlaintext", data=json.dumps(params), headers=headers)
    if(check_result(generateDataKeyWithoutPlaintext_resp, 'GenerateDataKeyWithoutPlaintext', 'test_GenerateDataKeyWithoutPlaintext') == False):
        return
    print('GenerateDataKeyWithoutPlaintext resp:\n%s\n' %(generateDataKeyWithoutPlaintext_resp.text))

    # test Decrypt(cipher_datakey)
    params=test_params({
            "aad": "test",
            "ciphertext": json.loads(generateDataKeyWithoutPlaintext_resp.text)['result']['ciphertext_base64'],
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
        })
    print('Decrypt req:\n%s\n' %(params))
    decrypt_resp = requests.post(url=base_url + "Decrypt", data=json.dumps(params), headers=headers)
    if(check_result(decrypt_resp, 'Decrypt', 'test_GenerateDataKeyWithoutPlaintext') == False):
        return
    print('Decrypt resp:\n%s\n' %(decrypt_resp.text))

    print('====================test_GenerateDataKeyWithoutPlaintext end===========================')

def test_GenerateDataKey(base_url, headers):
    print('====================test_GenerateDataKey start===========================')
    params=test_params({
            "keyspec":"EH_AES_GCM_128",
            "origin":"EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_GenerateDataKey') == False):
        return
    print('CreateKey resp:\n%s\n' %(create_resp.text))

    # test GenerateDataKey
    params=test_params({
            "aad": "test",
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "keylen": 16,
        })
    print('GenerateDataKey req:\n%s\n' %(params))
    generatedatakey_resp = requests.post(url=base_url + "GenerateDataKey", data=json.dumps(params), headers=headers)
    if(check_result(generatedatakey_resp, 'GenerateDataKey', 'test_GenerateDataKey') == False):
        return
    print('GenerateDataKey resp:\n%s\n' %(generatedatakey_resp.text))

    # test Decrypt(cipher_datakey)
    params=test_params({
            "aad": "test",
            "ciphertext": json.loads(generatedatakey_resp.text)['result']['ciphertext_base64'],
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
        })
    print('Decrypt req:\n%s\n' %(params))
    decrypt_resp = requests.post(url=base_url + "Decrypt", data=json.dumps(params), headers=headers)
    if(check_result(decrypt_resp, 'Decrypt', 'test_GenerateDataKey') == False):
        return
    print('Decrypt resp:\n%s\n' %(decrypt_resp.text))

    print('====================test_GenerateDataKey end===========================')

def test_AES128(base_url, headers):
    print('====================test_AES128 start===========================')
    params=test_params({
            "keyspec": "EH_AES_GCM_128",
            "origin": "EH_INTERNAL_KEY"
        })
    print('CreateKey req:\n%s\n' %(params))
    create_resp = requests.post(url=base_url + "CreateKey", data=json.dumps(params), headers=headers)
    if(check_result(create_resp, 'CreateKey', 'test_AES128') == False):
        return
    print('CreateKey resp:\n%s\n' %(create_resp.text))

    # test Encrypt("123456")
    params=test_params({
            "aad": "test",
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
            "plaintext": "123456",
        })
    print('Encrypt req:\n%s\n' %(params))
    encrypt_resp = requests.post(url=base_url + "Encrypt", data=json.dumps(params), headers=headers)
    if(check_result(encrypt_resp, 'Encrypt', 'test_AES128') == False):
        return
    print('Encrypt resp:\n%s\n' %(encrypt_resp.text))

    # test Decrypt(ciphertext)
    params=test_params({
            "aad": "test",
            "ciphertext": json.loads(encrypt_resp.text)['result']['ciphertext_base64'],
            "cmk_base64": json.loads(create_resp.text)['result']['cmk_base64'],
        })
    print('Decrypt req:\n%s\n' %(params))
    decrypt_resp = requests.post(url=base_url + "Decrypt", data=json.dumps(params), headers=headers)
    if(check_result(decrypt_resp, 'Decrypt', 'test_AES128') == False):
        return
    print('Decrypt resp:\n%s\n' %(decrypt_resp.text))
    
    plaintext = str(base64.b64decode(json.loads(decrypt_resp.text)['result']['plaintext_base64']), 'utf-8')
    print('Decrypt plaintext:\n%s\n' %(plaintext))
    print('check Decrypt plaintext result with %s: %s\n' %('123456', plaintext == '123456'))

    print('====================test_AES128 end===========================')

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip-adress', type=str, help='ip address of the ehsm_kms_server', required=True)
    parser.add_argument('-p', '--port', type=str, help='port of the ehsm_kms_server', required=True)
    args = parser.parse_args()
    ip = args.ip_adress
    port = args.port
    return ip, port
    
def check_result(res, action, test_name):
    res_json = json.loads(res.text)
    if(res_json['code'] == 200):
        print("%s successfully \n" %(action))
        return True
    else:
        print("%s failed, error message: %s \n" %(action, res_json["message"]))
        print('====================%s end===========================' %(test_name))
        return False
if __name__ == "__main__":
    headers = {"Content-Type":"application/json"}

    ip,port = get_args()

    base_url = "http://" + ip + ":" + port + "/ehsm?Action="

    test_creat_app_info(base_url, headers)

    test_AES128(base_url, headers)

    test_GenerateDataKey(base_url, headers)

    test_GenerateDataKeyWithoutPlaintext(base_url, headers)

    test_Stest_RSA3072_sign_verify(base_url, headers)

    test_RSA3072_encrypt_decrypt(base_url, headers)

    test_export_datakey(base_url, headers)