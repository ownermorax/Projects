import struct
import binascii

class SHA256:
    K = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]
    H0 = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.h = self.H0[:]
        self.message_length = 0
        self.buffer = b''
    
    @staticmethod
    def _right_rotate(n, b):
        return ((n >> b) | (n << (32 - b))) & 0xffffffff
    
    @staticmethod
    def _pad_message(message):
        length = len(message)
        message += b'\x80'
        message += b'\x00' * ((55 - length) % 64)
        message += struct.pack('>Q', length * 8)
        return message
    
    def _process_chunk(self, chunk):
        w = list(struct.unpack('>16L', chunk))
        for i in range(16, 64):
            s0 = self._right_rotate(w[i-15], 7) ^ self._right_rotate(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = self._right_rotate(w[i-2], 17) ^ self._right_rotate(w[i-2], 19) ^ (w[i-2] >> 10)
            w.append((w[i-16] + s0 + w[i-7] + s1) & 0xffffffff)
        a, b, c, d, e, f, g, h = self.h
        for i in range(64):
            s1 = self._right_rotate(e, 6) ^ self._right_rotate(e, 11) ^ self._right_rotate(e, 25)
            ch = (e & f) ^ ((~e) & g)
            temp1 = (h + s1 + ch + self.K[i] + w[i]) & 0xffffffff
            s0 = self._right_rotate(a, 2) ^ self._right_rotate(a, 13) ^ self._right_rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xffffffff
          
            h = g
            g = f
            f = e
            e = (d + temp1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xffffffff

        self.h[0] = (self.h[0] + a) & 0xffffffff
        self.h[1] = (self.h[1] + b) & 0xffffffff
        self.h[2] = (self.h[2] + c) & 0xffffffff
        self.h[3] = (self.h[3] + d) & 0xffffffff
        self.h[4] = (self.h[4] + e) & 0xffffffff
        self.h[5] = (self.h[5] + f) & 0xffffffff
        self.h[6] = (self.h[6] + g) & 0xffffffff
        self.h[7] = (self.h[7] + h) & 0xffffffff
    
    def update(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.message_length += len(data)
        self.buffer += data
        while len(self.buffer) >= 64:
            chunk = self.buffer[:64]
            self.buffer = self.buffer[64:]
            self._process_chunk(chunk)
    
    def digest(self):
        h_temp = self.h[:]
        length_temp = self.message_length
        buffer_temp = self.buffer
        padded = self._pad_message(buffer_temp)
        for i in range(0, len(padded), 64):
            chunk = padded[i:i+64]
            self._process_chunk(chunk)
        result = b''.join(struct.pack('>L', x) for x in self.h)
        self.h = h_temp
        self.message_length = length_temp
        self.buffer = buffer_temp
        return result
    
    def hexdigest(self):
        return binascii.hexlify(self.digest()).decode('ascii')
    
    def finalize(self):
        result = self.digest()
        self.reset()
        return result

def sha256(data):
    hasher = SHA256()
    hasher.update(data)
    return hasher.finalize()

def sha256_hex(data):
    hasher = SHA256()
    hasher.update(data)
    return hasher.hexdigest()

if __name__ == "__main__":
  text = "Hello"
  print(sha256_hex(text))
