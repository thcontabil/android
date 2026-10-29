"""O APK deve guardar somente campos financeiros mínimos da importação OFX."""
import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "site" / "py"))
from financas import bank, db, ofx  # noqa: E402


def sample_ofx():
    return ("OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\n\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS>"
            "<BANKACCTFROM><BANKID>1234<ACCTID>987654321<BANKTRANLIST>"
            "<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261010<TRNAMT>-25.00<FITID>TRANSACTION-ID-PRIVATE"
            "<NAME>PIX PARA JOAO DA SILVA CPF 12345678900</STMTTRN></BANKTRANLIST>"
            "<LEDGERBAL><BALAMT>100.00<DTASOF>20261010</LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>").encode()


class TestPrivacyOFX(unittest.TestCase):
    def test_parser_privado_descarta_identificadores_diretos(self):
        st = ofx.parse(sample_ofx(), privacy=True)
        self.assertEqual(st["account_label"], "Conta corrente")
        self.assertNotIn("987654321", st["account_key"])
        self.assertNotIn("1234", st["account_key"])
        self.assertEqual(st["txns"][0]["memo"], "PIX PARA")
        self.assertNotIn("TRANSACTION-ID-PRIVATE", st["txns"][0]["fitid"])
        self.assertNotIn("JOAO", st["txns"][0]["memo"])
        self.assertNotIn("12345678900", st["txns"][0]["memo"])

    def test_modo_privado_nao_persiste_identificadores_nem_nome_de_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "private.db")
            try:
                db.init(conn)
                raw = base64.b64encode(sample_ofx()).decode()
                with patch.dict(os.environ, {"MC_PRIVACY_MODE": "1"}):
                    result = bank.import_ofx(conn, {"data": raw, "filename": "extrato-Joao-987654321.ofx"})
                self.assertEqual(result["new"], 1)
                imp = conn.execute("SELECT filename, account_key, account_label FROM bank_imports").fetchone()
                txn = conn.execute("SELECT fitid, memo FROM bank_txns").fetchone()
                persisted = " ".join(str(v) for v in (*imp, *txn))
                for secret in ("Joao", "987654321", "12345678900", "TRANSACTION-ID-PRIVATE", "JOAO DA SILVA"):
                    self.assertNotIn(secret, persisted)
                self.assertEqual(imp[0], "extrato.ofx")
                self.assertEqual(imp[2], "Conta corrente")
                self.assertEqual(txn[1], "PIX PARA")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
