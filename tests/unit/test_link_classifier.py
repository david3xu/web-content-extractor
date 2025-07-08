import unittest
from unittest.mock import patch
from src.extractors.link_classifier import LinkClassifierService
from src.models.extraction_models import LinkType, ExtractedLink
from src.models.exceptions import LinkClassificationError


class TestLinkClassifierService(unittest.TestCase):
    def setUp(self):
        self.classifier = LinkClassifierService()

    def test_determine_link_type_pdf(self):
        # Test PDF link detection
        url = "https://example.com/document.pdf"
        link_type = self.classifier._determine_link_type(url)
        self.assertEqual(link_type, LinkType.PDF)

    def test_determine_link_type_youtube(self):
        # Test YouTube link detection
        youtube_urls = [
            "https://youtube.com/watch?v=12345",
            "https://youtu.be/12345",
            "https://youtube.com/embed/12345"
        ]

        for url in youtube_urls:
            link_type = self.classifier._determine_link_type(url)
            self.assertEqual(link_type, LinkType.YOUTUBE)

    def test_determine_link_type_other(self):
        # Test other link types
        url = "https://example.com/page.html"
        link_type = self.classifier._determine_link_type(url)
        self.assertEqual(link_type, LinkType.OTHER)

    def test_classify_links(self):
        # Setup
        links = [
            ("https://example.com/doc.pdf", "PDF Document"),
            ("https://youtube.com/watch?v=12345", "YouTube Video"),
            ("https://example.com/page.html", "Regular Page")
        ]

        # Execute
        classified_links = self.classifier.classify_links(links)

        # Assert
        self.assertEqual(len(classified_links), 3)

        # Check PDF link
        self.assertEqual(classified_links[0].url, "https://example.com/doc.pdf")
        self.assertEqual(classified_links[0].link_text, "PDF Document")
        self.assertEqual(classified_links[0].link_type, LinkType.PDF)

        # Check YouTube link
        self.assertEqual(classified_links[1].url, "https://youtube.com/watch?v=12345")
        self.assertEqual(classified_links[1].link_text, "YouTube Video")
        self.assertEqual(classified_links[1].link_type, LinkType.YOUTUBE)

        # Check other link
        self.assertEqual(classified_links[2].url, "https://example.com/page.html")
        self.assertEqual(classified_links[2].link_text, "Regular Page")
        self.assertEqual(classified_links[2].link_type, LinkType.OTHER)

    def test_classify_links_error(self):
        # Setup
        with patch.object(self.classifier, '_determine_link_type', side_effect=Exception("Test error")):
            # Execute & Assert
            with self.assertRaises(LinkClassificationError):
                self.classifier.classify_links([("https://example.com", "Example")])

    def test_categorize_by_type(self):
        # Setup
        links = [
            ExtractedLink(url="https://example.com/doc1.pdf", link_text="PDF1", link_type=LinkType.PDF),
            ExtractedLink(url="https://example.com/doc2.pdf", link_text="PDF2", link_type=LinkType.PDF),
            ExtractedLink(url="https://youtube.com/watch?v=1", link_text="YT1", link_type=LinkType.YOUTUBE),
            ExtractedLink(url="https://example.com/page.html", link_text="Page", link_type=LinkType.OTHER),
            ExtractedLink(url="https://youtube.com/watch?v=2", link_text="YT2", link_type=LinkType.YOUTUBE)
        ]

        # Execute
        pdf_links, youtube_links, other_links = self.classifier.categorize_by_type(links)

        # Assert
        self.assertEqual(len(pdf_links), 2)
        self.assertEqual(len(youtube_links), 2)
        self.assertEqual(len(other_links), 1)

        # Check content of each category
        self.assertEqual(pdf_links[0].link_text, "PDF1")
        self.assertEqual(pdf_links[1].link_text, "PDF2")

        self.assertEqual(youtube_links[0].link_text, "YT1")
        self.assertEqual(youtube_links[1].link_text, "YT2")

        self.assertEqual(other_links[0].link_text, "Page")


if __name__ == "__main__":
    unittest.main()
