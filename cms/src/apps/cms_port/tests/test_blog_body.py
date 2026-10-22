from django.test import SimpleTestCase, TestCase

from apps.cms_port.common import blog_body


class BlogBodyExpandTests(SimpleTestCase):
    def test_unwraps_container_content_div(self):
        from bs4 import BeautifulSoup

        html = (
            '<p>Lead</p>'
            '<div class="container content"><p>Inside</p></div>'
        )
        soup = BeautifulSoup(f'<div data-root>{html}</div>', 'lxml')
        root = soup.select_one('div[data-root]')
        nodes = blog_body._expand_body_nodes(root)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].name, 'p')
        self.assertEqual(nodes[1].name, 'p')


class BlogBodySanitizeTests(TestCase):
    def test_clean_html_preserves_heading_and_class(self):
        from bs4 import BeautifulSoup

        h2 = BeautifulSoup('<h2>Section</h2>', 'lxml').h2
        out = blog_body.blog_text_from_scrape_node(h2)
        self.assertIn('<h2>', out)
        self.assertIn('Section', out)

        p = BeautifulSoup('<p class="foo">Text</p>', 'lxml').p
        out = blog_body.blog_text_from_scrape_node(p)
        self.assertIn('Text', out)
        self.assertIn('class="foo"', out)

    def test_clean_html_keeps_inline_link(self):
        from bs4 import BeautifulSoup

        p = BeautifulSoup(
            '<p>See <a href="https://example.org/x">report</a>.</p>',
            'lxml',
        ).p
        out = blog_body.blog_text_from_scrape_node(p)
        self.assertIn('href="https://example.org/x"', out)
        self.assertIn('report', out)
