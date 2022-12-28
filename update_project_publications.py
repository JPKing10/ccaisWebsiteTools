from typing import List, Dict, Optional, Any
import multiprocessing
import logging
import requests
import re
import sys

NUM_PROCESSES = 8
PROJECT_ID = "520617"
PURE_PROJECT_UUID = "f7c56fc0-6c66-4e55-95c7-918bbf351b9f"
BASE_URL = "https://api-pure.soton.ac.uk"


class Publication:
    def __init__(self, pure_id: str, details: Dict[str, Any]):
        """Create publication from supplied details."""
        self.NO_DOI_LINK_DISPLAY = "Read more"
        self.AUTHOR_NAME_FORMAT = "{firstname} {lastname}"
        self.URL_REGEX = r"(https?:.*?)\""
        self.DOI_LINK_DISPLAY_REGEX = r"https?://doi.org/(.*)"

        self.pure_id = pure_id
        self.details = details
        self.link_url = ""
        self.link_display = ""

        self.title = details['title']
        self.authors = self._format_authors(details['persons'])
        doi = details['doi']
        if doi:
            self.add_link_from_doi(doi)
        else:
            self.add_link_from_harvard(details['harvard'])
        self.description = ""
        if not (self.title and self.authors and self.link_url):
            logging.warning("Unknown details for Pure ID: %s", pure_id)

    def _format_authors(self, persons: List[Dict[str, str]]) -> str:
        """Extract authors and add their name to the authors string in "Firstname Lastname" format."""
        authors = [self.AUTHOR_NAME_FORMAT.format(firstname=x['firstname'], lastname=x['lastname'])
                   if x['role'] == "Author" else None for x in persons]
        return ", ".join(authors)

    def add_link_from_doi(self, doi: str):
        """Set link and display text from specified DOI link"""
        doi_number = re.findall(self.DOI_LINK_DISPLAY_REGEX, doi)
        if len(doi_number) == 0:
            logging.warning("Bad DOI %s", doi)
            return
        if 1 < len(doi_number):
            logging.warning("Too many display options for DOI %s for Pure ID %s: %s", doi, self.pure_id, doi_number)
        self.link_url = doi
        self.link_display = doi_number[0]

    def add_link_from_harvard(self, harvard: str):
        """Extract URLs from Harvard text and use the first as the link for this publication"""
        urls = re.findall(self.URL_REGEX, harvard)
        if len(urls) == 0:
            logging.warning("No URLs found in Harvard text for Pure ID: %s", self.pure_id)
            return
        if "eprints.soton.ac.uk" not in urls[0]:
            logging.warning("Found non eprints.soton.ac.uk link in Harvard text for Pure ID %s: %s", self.pure_id,
                            urls[0])
        self.link_url = urls[0]
        self.link_display = self.NO_DOI_LINK_DISPLAY

    def __str__(self):
        """Yaml formatted publication string."""
        pub_str = ""
        pub_str += "- title: \"" + self.title + "\"\n"
        pub_str += "  description: " + self.description + "\n"
        pub_str += "  authors: " + self.authors + "\n"
        pub_str += "  link:\n"
        pub_str += "    url: " + self.link_url + "\n"
        pub_str += "    display: " + self.link_display + "\n"
        return pub_str


def rest_get(base_url: str, endpoint: str, query: str) -> Optional[Dict[str, Any]]:
    """Execute GET request and return the json content."""
    url = base_url + "/" + endpoint + "/" + query
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error("GET Did not succeed with status code %s\n\t Request: %s", response.status_code, url)
        return None
    return response.json()


def get_publication_ids() -> List[str]:
    """A list of the publication Pure IDs."""
    project_publications = rest_get(BASE_URL, "project", PROJECT_ID)
    if project_publications is None:
        raise Exception("Could not retrieve publication IDs")
    publication_ids = []
    for publication in project_publications['outputs']:
        publication_ids.append(publication['pureId'])
    return publication_ids


def enrich_publication(pure_id: str) -> Optional[Publication]:
    """Create a publication from the specified Pure ID."""
    publication_details = rest_get(BASE_URL, ".", "outputs?limit=1&offset=0&guids=" + pure_id)
    if publication_details is None:
        logging.error("Could not retrieve details for publication with Pure ID: %s", pure_id)
        return None
    if publication_details['count'] != 1:
        logging.error("Unexpected publication details for Pure ID: %s", pure_id)
        return None
    details = publication_details['publications'][0]
    return Publication(pure_id, details)


def write_publications(output_path: str, publications: List[Publication]):
    """Write publications to file at specified output path."""
    with open(output_path, 'w') as f:
        for p in publications:
            f.write(p.__str__())
            f.write("\n")


def main(output_path: Optional[str] = None):
    publication_ids = get_publication_ids()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        publications = pool.map(enrich_publication, publication_ids)
    if output_path:
        write_publications(output_path, publications)
    else:
        for p in publications:
            print(p)


if __name__ == '__main__':
    if 1 < len(sys.argv):
        main(sys.argv[1])
    else:
        main()
