import asyncio
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import designer

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.orig = agent._client
        self.orig_fallback = agent.ALLOW_OFFLINE_FALLBACK
        agent.ALLOW_OFFLINE_FALLBACK = True
        agent._client = None  # API trafik yubormasdan sinash
    def tearDown(self):
        agent._client = self.orig
        agent.ALLOW_OFFLINE_FALLBACK = self.orig_fallback

    def ask(self, text, prev=None):
        return asyncio.run(agent.analyze(text, prev))

    def test_ayub(self):
        x=self.ask('manga Ayub degan sozga logo kere')
        self.assertEqual(x['brand'],'Ayub')
        self.assertEqual(x['mode'],'new')

    def test_ayub_apostrophe(self):
        self.assertEqual(self.ask("Ayub degan so'zga logo kerak")['brand'],'Ayub')

    def test_mycoffee(self):
        self.assertEqual(self.ask('My Coffee uchun zamonaviy logo')['brand'],'My Coffee')

    def test_cmbk(self):
        self.assertEqual(self.ask('Ali CMBK uchun premium logo, oltin rangda')['brand'],'Ali CMBK')

    def test_standalone_name(self):
        self.assertEqual(self.ask('Ayub')['brand'],'Ayub')

    def test_color_edit(self):
        prev=self.ask('Ayub')
        x=self.ask("rangini ko'k qil",prev)
        self.assertEqual(x['brand'],'Ayub')
        self.assertEqual(x['mode'],'edit')
        self.assertEqual(x['palette'],'navy_ice')

    def test_minimal_edit(self):
        prev=self.ask('Ayub')
        x=self.ask('minimal qil',prev)
        self.assertEqual(x['brand'],'Ayub')
        self.assertEqual(x['border'],False)

    def test_next_brand(self):
        prev=self.ask('Ayub')
        x=self.ask('My Coffee uchun logo',prev)
        self.assertEqual(x['mode'],'new')
        self.assertEqual(x['brand'],'My Coffee')

    def test_hello(self):
        self.assertEqual(self.ask('salom')['mode'],'chat')
        self.assertEqual(self.ask('rahmat')['mode'],'chat')

    def test_no_brand_edit(self):
        self.assertEqual(self.ask("rangini ko'k qil")['mode'],'chat')

    def test_false_ai_response_preserves_brand(self):
        raw={'mode':'edit','brand':'Ayub','palette':'navy_ice'}
        x=agent.sanitize(raw,{'brand':'Ayub','symbol':'shield','palette':'black_gold','font':'bold','layout':'wordmark','border':False})
        self.assertEqual(x['symbol'],'shield')
        self.assertEqual(x['layout'],'wordmark')
        self.assertEqual(x['border'],False)

    def test_remove_symbol(self):
        p=self.ask('Ayub')
        self.assertEqual(self.ask('belgini olib tashla',p)['layout'],'wordmark')

    def test_quoted_name(self):
        prev=self.ask('Ayub')
        self.assertEqual(self.ask("faqat 'Nova Tech' yozuvi tushsin",prev)['brand'],'Nova Tech')

    def test_only_text_edit(self):
        prev=self.ask('Ayub')
        spec=self.ask('faqat yozuv qolsin',prev)
        self.assertEqual(spec['brand'],'Ayub')
        self.assertEqual(spec['mode'],'edit')
        self.assertEqual(spec['layout'],'wordmark')

    def test_no_name_new(self):
        self.assertEqual(self.ask('Yangi logo kerak')['mode'],'chat')

    def test_storage(self):
        import tempfile
        import storage
        from pathlib import Path
        orig_dir, orig_db = storage.DATA_DIR, storage.DATABASE
        with tempfile.TemporaryDirectory() as d:
            try:
                storage.DATA_DIR=Path(d)
                storage.DATABASE=Path(d)/'test.sqlite3'
                storage.init_db()
                storage.save_spec(123, self.ask('Ayub'))
                self.assertEqual(storage.get_spec(123)['brand'],'Ayub')
                storage.reset_spec(123)
                self.assertIsNone(storage.get_spec(123))
            finally:
                storage.DATA_DIR, storage.DATABASE=orig_dir, orig_db


    def test_offline_does_not_pretend_ai(self):
        agent.ALLOW_OFFLINE_FALLBACK = False
        x = self.ask('Ayub uchun logo')
        self.assertEqual(x['mode'], 'chat')
        self.assertIn('Gemini', x['reply'])

    def test_rename(self):
        self.assertEqual(agent.rename_request("nomini Temurga o'zgartir"), 'Temur')
        self.assertEqual(agent.rename_request("nomini DNYR Studio deb o'zgartir"), 'DNYR Studio')

    def test_model_chat_response(self):
        from unittest.mock import patch
        agent._client = object()
        with patch.object(agent, '_call_ai', return_value={"mode":"chat", "reply":"Assalomu alaykum, logo nomini ayting."}):
            res = self.ask('Menga shunchaki maslahat bering')
        self.assertEqual(res['mode'], 'chat')

    def test_model_brand_from_natural_language(self):
        from unittest.mock import patch
        agent._client = object()
        with patch.object(agent, '_call_ai', return_value={"mode":"new", "brand":"Ziyo Academy", "style":"ta'lim", "palette":"navy_ice"}):
            res = self.ask("Bolalar o'qitiladigan o'quv markazimga bir logotip chiz, uning ismi Ziyo Academy")
        self.assertEqual(res['brand'], 'Ziyo Academy')
        self.assertEqual(res['_engine'], 'AI')

    def test_model_edit_preserves_original(self):
        from unittest.mock import patch
        agent._client = object()
        prev = agent.fallback_agent('Ayub uchun gaming logo')
        with patch.object(agent, '_call_ai', return_value={"mode":"edit", "palette":"navy_ice"}):
            res = self.ask("Rangini ko'k qil, qolganini o'zgartirma", prev)
        self.assertEqual(res['brand'], 'Ayub')
        self.assertEqual(res['palette'], 'navy_ice')
        self.assertEqual(res['symbol'], prev['symbol'])

    def test_model_failure_clearly_explained(self):
        from unittest.mock import patch
        agent._client = object()
        agent.ALLOW_OFFLINE_FALLBACK = False
        with patch.object(agent, '_call_ai', side_effect=RuntimeError('API not working')):
            res = self.ask('Ayub uchun logo')
        self.assertEqual(res['mode'], 'chat')
        self.assertIn('/testai', res['reply'])

    def test_png_render(self):
        from PIL import Image
        from io import BytesIO
        data=designer.render(self.ask('Ayub'),seed=7)
        im=Image.open(BytesIO(data))
        self.assertEqual(im.size,(1024,1024))
        self.assertEqual(im.format,'PNG')

if __name__=='__main__':unittest.main()
