from cryptography.fernet import Fernet

class EncryptDecrypt:
    def __init__( self ):
        pass

    def createKeyAndSave( self, pathnfile:str ):
        """
        Creates a new crypt key and saves it to the given pathnfile.
        The file may only have one line which contains the key.
        Needs to be run only once. Read the file (the key) whenever you want to decrypt
        a string previously encrypted using this key.
        """
        key:bytes = Fernet.generate_key()
        with open( pathnfile, "wb", ) as key_file:
            key_file.write( key )

    def getKey( self, pathnfile:str ) -> bytes:
        """
        Read the crypt key from the given file.
        """
        with open( pathnfile, "rb" ) as keyfile:
            return keyfile.read()

    def encryptAndStore( self, key: bytes, strToEncrypt: str, pathnfile: str ):
        """
        Encrypts <strToEncrypt> using <key> and stores it to <pathnfile>
        :param key:
        :param strToEncrypt:
        :param pathnfile:
        :return: None
        """
        with open( pathnfile, "wb" ) as file_enc:
            file_enc.write( self.encrypt( key, strToEncrypt ) )

    def encrypt( self, key:bytes, strToEncrypt: str ) -> bytes:
        """
        Encrypts the given string <strToEncrypt> using  key and returns it encrypted
        """
        f = Fernet( key )
        encoded:bytes = strToEncrypt.encode() #convert s to bytes using utf-8 codec
        encrypted:bytes = f.encrypt( encoded )
        return encrypted

    def decryptEncrypted( self, key:bytes, enc_str:bytes ) -> bytes:
        """
        Decrypts an encrypted string enc_str using key and returns the decrypted bytes.
        """
        f = Fernet( key )
        return f.decrypt( enc_str )

    def getDecryptedFromFile( self, key:bytes, enc_pathnfile:str ) -> bytes:
        """
        Reads a file containing an encrypted content and decrypts this content using key.
        """
        with open( enc_pathnfile, "rb" ) as enc_file:
            encrypted = enc_file.read()
        return self.decryptEncrypted( key, encrypted )

def testEncrypt():
    key = b"_="
    ed = EncryptDecrypt()
    pwd_enc = ed.encrypt( key, "" )
    print( pwd_enc.decode() )

def test():
    path = ""
    keyfile = ""
    userfile = ""
    pwdfile = ""
    crypt = EncryptDecrypt()
    key = crypt.getKey( path + keyfile )
    user = crypt.getDecryptedFromFile( key, path + userfile ).decode()
    pwd = crypt.getDecryptedFromFile( key, path + pwdfile ).decode()
    print( user, ": ", pwd )