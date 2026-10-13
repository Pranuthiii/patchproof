def test_path_traversal_blocked(self):
       payloads = ["../secret.txt", "../../secret.txt", "..\\..\\secret.txt"]  # maybe just one type
       for payload in payloads:
           with self.subTest(payload=payload):
               with self.assertRaises((FileNotFoundError, ValueError, ...)) as cm:
                   read_attachment(self.base, payload)
