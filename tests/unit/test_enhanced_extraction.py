from src.infrastructure.html_parser import BeautifulSoupLinkParser


class TestEnhancedExtraction:
    def test_pdf_download_detection(self) -> None:
        """Test PDF download link detection"""
        html = """
        <a class="group/file flex flex-row items-center px-5 py-3" download="Full_Stack_AI_Engineer_Bootcamp_Dev_Setup.pdf" href="https://1402095927-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FqphMrpYu5rzFU5LRkIrP%2Fuploads%2FfBn6B997...">
            Full_Stack_AI_Engineer_Bootcamp_Dev_Setup.pdf
        </a>
        """

        parser = BeautifulSoupLinkParser()
        links = parser.parse_links(html, "https://example.com")

        assert len(links) == 1
        assert (
            links[0][1] == "Full_Stack_AI_Engineer_Bootcamp_Dev_Setup.pdf"
        )  # Assert on exact link_text

    def test_youtube_iframe_detection(self) -> None:
        """Test YouTube iframe detection"""
        html = """
        <iframe src="https://cdn.iframe.ly/CXHbSqy" style="top: 0; left: 0; width: 100%; height: 100%; position: absolute; border: 0;">
        </iframe>
        """

        parser = BeautifulSoupLinkParser()
        links = parser.parse_links(html, "https://example.com")

        assert len(links) == 1
        assert "iframe.ly" in links[0][0]
        assert "Embedded Video" in links[0][1]
