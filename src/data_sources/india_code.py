"""
India Code Data Source (indiacode.nic.in)

Official repository of all Indian legislation. This module fetches bare acts
and builds the critical IPC ↔ BNS section mapping table.
"""

import json
import logging
import re
from typing import Generator, Optional
from pathlib import Path
from bs4 import BeautifulSoup

from src.data_sources.base import (
    BaseDataSource, DataSourceConfig, DocumentType, ScrapedDocument, SourceName,
)

logger = logging.getLogger(__name__)

# === OFFICIAL IPC to BNS MAPPING ===
# From MHA Gazette Notification (1 July 2024)
IPC_TO_BNS = {
    # Offences affecting human body - Homicide
    "299": "100",  # Culpable homicide
    "300": "101",  # Murder
    "301": "102",  # Culpable homicide by causing death of other
    "302": "103",  # Punishment for murder
    "303": "103(2)",  # Murder by life convict (merged)
    "304": "105",  # Punishment for culpable homicide
    "304A": "106",  # Death by negligence
    "304B": "80",   # Dowry death
    "306": "108",  # Abetment of suicide
    "307": "109",  # Attempt to murder
    "308": "110",  # Attempt to culpable homicide
    "309": "None",  # Attempt to suicide (decriminalized)

    # Hurt
    "319": "114",  # Hurt
    "320": "115",  # Grievous hurt
    "321": "114",  # Voluntarily causing hurt
    "322": "115",  # Voluntarily causing grievous hurt
    "323": "115(2)",  # Punishment for voluntarily causing hurt
    "324": "118(1)",  # Voluntarily causing hurt by dangerous weapons
    "325": "117(2)",  # Punishment for grievous hurt
    "326": "118(2)",  # Grievous hurt by dangerous weapons
    "326A": "124",  # Acid attack
    "326B": "125",  # Attempt to acid attack

    # Wrongful restraint and confinement
    "339": "126",  # Wrongful restraint
    "340": "127",  # Wrongful confinement
    "341": "126(2)",  # Punishment for wrongful restraint
    "342": "127(2)",  # Punishment for wrongful confinement
    "343": "127(3)",  # Wrongful confinement 3+ days
    "344": "127(4)",  # Wrongful confinement 10+ days
    "346": "128",  # Wrongful confinement in secret
    "347": "129",  # Wrongful confinement for extortion
    "348": "130",  # Wrongful confinement for confession

    # Criminal force and assault
    "349": "131",  # Force
    "350": "131",  # Criminal force
    "351": "131",  # Assault
    "352": "131(2)",  # Punishment for assault
    "353": "132",  # Assault on public servant
    "354": "74",   # Assault/criminal force on woman
    "354A": "75",  # Sexual harassment
    "354B": "76",  # Assault with intent to disrobe woman
    "354C": "77",  # Voyeurism
    "354D": "78",  # Stalking

    # Kidnapping
    "359": "135",  # Kidnapping
    "360": "136",  # Kidnapping from India
    "361": "137",  # Kidnapping from lawful guardian
    "362": "138",  # Abduction
    "363": "137(2)",  # Punishment for kidnapping
    "363A": "141",  # Kidnapping for begging
    "364": "140(1)",  # Kidnapping for murder
    "364A": "140(2)",  # Kidnapping for ransom
    "365": "140(3)",  # Kidnapping to secretly confine
    "366": "139",  # Kidnapping woman to compel marriage
    "366A": "139(2)",  # Procuration of minor girl
    "366B": "139(3)",  # Importation of girl
    "367": "140",  # Kidnapping for grievous hurt
    "368": "140",  # Concealing kidnapped person
    "369": "141",  # Kidnapping child under 10

    # Sexual offences
    "375": "63",   # Rape
    "376": "64",   # Punishment for rape
    "376A": "66",  # Death or vegetative state after rape
    "376AB": "65(1)",  # Rape on woman under 12
    "376B": "67",  # Intercourse by husband during separation
    "376C": "68",  # Intercourse by person in authority
    "376D": "70",  # Gang rape
    "376DA": "70(2)",  # Gang rape on woman under 16
    "376DB": "70(2)",  # Gang rape on woman under 12
    "376E": "71",  # Repeat offenders

    # Theft
    "378": "303",  # Theft
    "379": "303(2)",  # Punishment for theft
    "380": "305(a)",  # Theft in dwelling house
    "381": "305(b)",  # Theft by clerk or servant
    "382": "305(c)",  # Theft after preparation for hurt

    # Robbery and Dacoity
    "390": "309",  # Robbery
    "391": "310",  # Dacoity
    "392": "309(2)",  # Punishment for robbery
    "393": "309(3)",  # Attempt to commit robbery
    "394": "309(4)",  # Voluntarily causing hurt in robbery
    "395": "310(2)",  # Punishment for dacoity
    "396": "310(3)",  # Dacoity with murder
    "397": "311",  # Robbery with attempt to cause death
    "398": "311",  # Attempt to commit robbery with deadly weapon
    "399": "312",  # Making preparation for dacoity
    "400": "313",  # Punishment for belonging to gang of dacoits
    "401": "314",  # Belonging to gang of thieves
    "402": "315",  # Assembling for dacoity

    # Criminal misappropriation and breach of trust
    "403": "316",  # Dishonest misappropriation
    "404": "317",  # Misappropriation by finding
    "405": "316",  # Criminal breach of trust
    "406": "316(2)",  # Punishment for breach of trust
    "407": "316(3)",  # Breach of trust by carrier
    "408": "316(4)",  # Breach of trust by clerk/servant
    "409": "316(5)",  # Breach of trust by public servant

    # Cheating
    "415": "318",  # Cheating
    "416": "319",  # Cheating by personation
    "417": "318(2)",  # Punishment for cheating
    "418": "318(3)",  # Cheating with knowledge of wrongful loss
    "419": "319(2)",  # Punishment for cheating by personation
    "420": "318(4)",  # Cheating and dishonestly inducing delivery

    # Mischief
    "425": "324",  # Mischief
    "426": "324(2)",  # Punishment for mischief
    "427": "324(3)",  # Mischief causing damage > 50
    "435": "326",  # Mischief by fire with intent to cause damage
    "436": "326(2)",  # Mischief by fire to destroy house

    # Criminal trespass
    "441": "329",  # Criminal trespass
    "442": "330",  # House trespass
    "443": "331",  # Lurking house trespass
    "447": "329(2)",  # Punishment for criminal trespass
    "448": "330(2)",  # Punishment for house trespass
    "449": "331(2)",  # House trespass to commit offence punishable with death
    "450": "331(3)",  # House trespass to commit imprisonment
    "451": "331(4)",  # House trespass to commit cognizable offence
    "452": "331(5)",  # House trespass after preparation for hurt
    "453": "331(6)",  # Punishment for lurking house trespass
    "454": "331(7)",  # Lurking house trespass to commit cognizable offence
    "456": "332",  # Night trespass

    # Forgery
    "463": "336",  # Forgery
    "464": "337",  # Making false document
    "465": "336(2)",  # Punishment for forgery
    "467": "338",  # Forgery of valuable security
    "468": "340",  # Forgery for cheating
    "471": "341",  # Using forged document as genuine

    # Criminal intimidation
    "503": "351",  # Criminal intimidation
    "506": "351(2)(3)",  # Punishment for criminal intimidation
    "507": "351(4)",  # Criminal intimidation by anonymous communication

    # Offences relating to marriage
    "493": "82",   # Cohabitation by deceitful marriage
    "494": "82",   # Bigamy
    "495": "83",   # Concealment of former marriage
    "496": "84",   # Fraudulent marriage
    "497": "None",  # Adultery (decriminalized by SC)
    "498": "85",   # Enticing married woman
    "498A": "85",  # Cruelty by husband/relatives (dowry)

    # Defamation
    "499": "356",  # Defamation
    "500": "356(2)",  # Punishment for defamation

    # Attempt
    "511": "62",   # Attempt to commit offences punishable with imprisonment for life

    # Abetment
    "107": "45",   # Abetment
    "108": "46",   # Abettor
    "109": "48",   # Punishment for abetment
    "110": "49",   # Punishment for abetment if not otherwise provided
    "111": "50",   # Abettor when one act abetted and different act done
    "113": "51",   # Abettor present when offence committed
    "114": "52",   # Abettor present when offence committed
    "115": "53",   # Abetment of offence punishable with death/imprisonment for life
    "116": "54",   # Abetment of offence punishable with imprisonment
    "117": "55",   # Abetting commission of offence by public
    "118": "56",   # Concealing design to commit offence punishable with death
    "119": "57",   # Concealing design to commit punishable with imprisonment
    "120A": "61",  # Criminal conspiracy
    "120B": "61(2)",  # Punishment for criminal conspiracy

    # Public tranquility
    "141": "189",  # Unlawful assembly
    "143": "189(2)",  # Punishment for unlawful assembly
    "144": "189(3)",  # Joining unlawful assembly armed
    "145": "189(4)",  # Joining unlawful assembly after command to disperse
    "146": "190",  # Rioting
    "147": "190(2)",  # Punishment for rioting
    "148": "190(3)",  # Rioting armed with deadly weapon
    "149": "191",  # Every member of unlawful assembly guilty
    "153": "192",  # Provocation with intent to cause riot
    "153A": "196",  # Promoting enmity between groups

    # Offences by public servants
    "166": "202",  # Public servant disobeying law
    "166A": "202",  # Non-treatment by hospital
    "167": "203",  # Public servant framing incorrect record
    "168": "204",  # Public servant unlawfully engaging in trade
    "169": "205",  # Public servant unlawfully buying/bidding
    "170": "206",  # Personating a public servant
    "171": "207",  # Wearing garb of public servant
}

# CrPC to BNSS mapping (key sections)
CRPC_TO_BNSS = {
    "41": "35",    # When police may arrest without warrant
    "41A": "35",   # Notice of appearance before police
    "57": "58",    # Person arrested not to be detained more than 24 hours
    "154": "173",  # Information in cognizable cases (FIR)
    "155": "174",  # Information as to non-cognizable cases
    "156": "175",  # Police officer's power to investigate cognizable case
    "157": "176",  # Procedure for investigation
    "160": "179",  # Police officer's power to require attendance of witnesses
    "161": "180",  # Examination of witnesses by police
    "162": "181",  # Statements to police not to be signed
    "163": "182",  # No inducement to be offered
    "164": "183",  # Recording of confessions and statements
    "165": "185",  # Search by police officer
    "166": "186",  # When officer in charge may require search
    "167": "187",  # Procedure when investigation not completed in 24 hours
    "169": "189",  # Release of accused when evidence not sufficient
    "170": "190",  # Cases to be sent to Magistrate when evidence sufficient
    "173": "193",  # Report of police officer (Chargesheet)
    "174": "194",  # Police to inquire and report on suicide
    "175": "195",  # Power to summon persons
    "176": "196",  # Inquiry by Magistrate into cause of death
    "190": "210",  # Cognizance of offences by Magistrate
    "197": "218",  # Prosecution of Judges and public servants
    "200": "223",  # Examination of complainant
    "202": "225",  # Postponement of issue of process
    "204": "227",  # Issue of process
    "207": "230",  # Supply of copy of police report
    "216": "239",  # Power to alter charge
    "225": "248",  # Trial before sessions court
    "227": "250",  # Discharge
    "228": "251",  # Framing of charge
    "232": "255",  # Acquittal
    "233": "256",  # Conviction
    "235": "258",  # Judgment of acquittal/conviction
    "236": "259",  # Previous conviction
    "237": "260",  # Procedure when Magistrate not competent
    "238": "261",  # Compliance with Section 207
    "239": "262",  # When accused shall be discharged
    "240": "263",  # Framing of charge
    "241": "264",  # Conviction on plea of guilty
    "242": "265",  # Evidence for prosecution
    "243": "266",  # Evidence for defence
    "244": "267",  # Evidence for prosecution in warrant trial
    "245": "268",  # When accused shall be acquitted
    "246": "269",  # Procedure where accused is not acquitted
    "247": "270",  # Evidence for defence
    "248": "271",  # Acquittal or conviction
    "250": "273",  # Compensation for accusation without reasonable cause
    "251": "274",  # Substance of accusation to be stated
    "252": "275",  # Conviction on plea of guilty
    "253": "276",  # Conviction on plea of not guilty
    "313": "351",  # Power to examine accused
    "315": "353",  # Accused person as witness
    "317": "355",  # Provision for inquiries and trials being held in absence
    "319": "357",  # Power to proceed against other persons
    "320": "359",  # Compounding of offences
    "353": "393",  # Judgment to be in writing
    "354": "394",  # Language of judgment
    "357": "395",  # Order to pay compensation
    "357A": "396",  # Victim compensation scheme
    "358": "397",  # Compensation to accused in groundless cases
    "374": "413",  # Appeals from convictions
    "378": "417",  # Appeal in case of acquittal
    "389": "428",  # Suspension of sentence pending appeal
    "390": "429",  # Arrest of accused in appeal from acquittal
    "397": "436",  # Calling for records to examine legality
    "399": "438",  # Sessions Judge's or HC's powers of revision
    "401": "440",  # HC's powers of revision
    "428": "469",  # Period of detention to be set off against sentence
    "432": "473",  # Power to suspend or remit sentences
    "436": "478",  # Bail in bailable offences
    "436A": "479",  # Maximum period for which undertrial can be detained
    "437": "480",  # When bail may be taken in non-bailable offences
    "438": "482",  # Direction for grant of anticipatory bail
    "439": "483",  # Special powers of HC or Court of Session regarding bail
    "440": "484",  # Amount of bond and reduction thereof
    "441": "485",  # Bond of accused and sureties
    "468": "512",  # Bar to taking cognizance after lapse of period
    "482": "528",  # Saving of inherent powers of High Court
}

# Indian Evidence Act to Bharatiya Sakshya Adhiniyam
IEA_TO_BSA = {
    "3": "2",     # Interpretation
    "4": "3",     # May presume
    "5": "4",     # Relevancy of facts
    "6": "5",     # Res gestae
    "7": "6",     # Facts forming part of same transaction
    "8": "7",     # Motive, preparation, conduct
    "9": "8",     # Explanatory or introductory facts
    "17": "15",   # Admission
    "21": "19",   # Proof of admission against maker
    "24": "22",   # Confession caused by inducement
    "25": "23",   # Confession to police not provable
    "26": "24",   # Confession by accused in custody
    "27": "25",   # How much of discovery information admissible
    "32": "26",   # Dying declaration
    "45": "39",   # Expert opinion
    "46": "40",   # Expert opinion on foreign law
    "47": "41",   # Opinion as to handwriting
    "57": "51",   # Facts of which Court must take judicial notice
    "59": "53",   # Proof of facts by oral evidence
    "60": "54",   # Oral evidence must be direct
    "61": "55",   # Proof of contents of documents
    "62": "56",   # Primary evidence
    "63": "57",   # Secondary evidence
    "65": "58",   # When secondary evidence may be given
    "65A": "59",  # Special provisions for electronic record
    "65B": "63",  # Admissibility of electronic records (CRITICAL)
    "73": "69",   # Comparison of handwriting
    "101": "104", # Burden of proof
    "102": "105", # On whom burden lies
    "103": "106", # Burden on particular fact
    "105": "108", # Burden of proving exception
    "106": "109", # Burden on accused with special knowledge
    "112": "115", # Birth during marriage conclusive proof
    "113A": "118",# Presumption as to abetment of suicide
    "113B": "119",# Presumption as to dowry death
    "114": "120", # Court may presume existence of certain facts
    "114A": "121",# Presumption as to consent in prosecution for rape
    "133": "131", # Accomplice
    "134": "132", # Number of witnesses
    "137": "135", # Examination-in-chief
    "138": "136", # Cross-examination
    "139": "137", # Re-examination
    "145": "143", # Cross-examination as to previous statements
    "154": "151", # Questions by party to own witness
    "155": "152", # Impeaching credit of witness
}


class IndiaCodeDataSource(BaseDataSource):
    """
    Fetches bare act texts from India Code (indiacode.nic.in)
    and provides section mapping between old and new criminal codes.
    """

    BASE_URL = "https://www.indiacode.nic.in"

    def source_name(self) -> SourceName:
        return SourceName.INDIA_CODE

    def get_section_mapping(self, direction: str = "ipc_to_bns") -> dict:
        """
        Get section mapping between old and new codes.

        Args:
            direction: "ipc_to_bns", "bns_to_ipc", "crpc_to_bnss",
                      "bnss_to_crpc", "iea_to_bsa", "bsa_to_iea"
        """
        mappings = {
            "ipc_to_bns": IPC_TO_BNS,
            "bns_to_ipc": {v: k for k, v in IPC_TO_BNS.items() if v != "None"},
            "crpc_to_bnss": CRPC_TO_BNSS,
            "bnss_to_crpc": {v: k for k, v in CRPC_TO_BNSS.items()},
            "iea_to_bsa": IEA_TO_BSA,
            "bsa_to_iea": {v: k for k, v in IEA_TO_BSA.items()},
        }
        return mappings.get(direction, {})

    def convert_section(self, section: str, from_code: str = "IPC", to_code: str = "BNS") -> Optional[str]:
        """
        Convert a section number from one code to another.

        Examples:
            convert_section("302", "IPC", "BNS") -> "103"
            convert_section("103", "BNS", "IPC") -> "302"
        """
        direction_map = {
            ("IPC", "BNS"): "ipc_to_bns",
            ("BNS", "IPC"): "bns_to_ipc",
            ("CrPC", "BNSS"): "crpc_to_bnss",
            ("BNSS", "CrPC"): "bnss_to_crpc",
            ("IEA", "BSA"): "iea_to_bsa",
            ("BSA", "IEA"): "bsa_to_iea",
        }
        direction = direction_map.get((from_code.upper(), to_code.upper()))
        if not direction:
            return None
        mapping = self.get_section_mapping(direction)
        return mapping.get(section)

    def save_mappings(self, output_dir: str = "configs"):
        """Save all code mappings as JSON files for the system to use."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        mappings = {
            "ipc_to_bns": IPC_TO_BNS,
            "crpc_to_bnss": CRPC_TO_BNSS,
            "iea_to_bsa": IEA_TO_BSA,
        }

        for name, mapping in mappings.items():
            filepath = output / f"{name}_mapping.json"
            with open(filepath, "w") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved mapping: {filepath} ({len(mapping)} entries)")

        # Also save reverse mappings
        for name, mapping in mappings.items():
            reverse_name = name.replace("_to_", "_from_")
            reverse_mapping = {v: k for k, v in mapping.items() if v != "None"}
            filepath = output / f"{reverse_name}_mapping.json"
            with open(filepath, "w") as f:
                json.dump(reverse_mapping, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved reverse mapping: {filepath} ({len(reverse_mapping)} entries)")

    def fetch_act_sections(self, act_id: str) -> Generator[dict, None, None]:
        """Fetch sections of a specific act from India Code."""
        url = f"{self.BASE_URL}/show-data"
        params = {"actid": act_id, "type": "section"}
        response = self.fetch_page(url, params=params)
        if not response:
            return

        soup = BeautifulSoup(response.text, "lxml")
        sections = soup.select(".section-item") or soup.select("tr")

        for section in sections:
            section_num = section.select_one(".section-number")
            section_title = section.select_one(".section-title")
            section_text = section.select_one(".section-text")

            yield {
                "number": section_num.get_text(strip=True) if section_num else "",
                "title": section_title.get_text(strip=True) if section_title else "",
                "text": section_text.get_text(strip=True) if section_text else "",
            }

    def scrape(
        self,
        acts: list[str] = None,
        save_mappings: bool = True,
        **kwargs,  # Accept additional kwargs (e.g., max_results_per_query) for compatibility
    ) -> Generator[ScrapedDocument, None, None]:
        """
        Scrape bare act texts and save section mappings.
        """
        if save_mappings:
            self.save_mappings()

        # Key acts to scrape
        act_configs = [
            {"id": "IPC", "name": "Indian Penal Code, 1860", "url_path": "/handle/123456789/2263"},
            {"id": "BNS", "name": "Bharatiya Nyaya Sanhita, 2023", "url_path": "/handle/123456789/20062"},
            {"id": "CrPC", "name": "Code of Criminal Procedure, 1973", "url_path": "/handle/123456789/1362"},
            {"id": "BNSS", "name": "Bharatiya Nagarik Suraksha Sanhita, 2023", "url_path": "/handle/123456789/20063"},
            {"id": "IEA", "name": "Indian Evidence Act, 1872", "url_path": "/handle/123456789/2188"},
            {"id": "BSA", "name": "Bharatiya Sakshya Adhiniyam, 2023", "url_path": "/handle/123456789/20064"},
            {"id": "NDPS", "name": "Narcotic Drugs and Psychotropic Substances Act, 1985", "url_path": "/handle/123456789/1791"},
            {"id": "POCSO", "name": "Protection of Children from Sexual Offences Act, 2012", "url_path": "/handle/123456789/15532"},
            {"id": "SCST", "name": "Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989", "url_path": "/handle/123456789/1744"},
            {"id": "ArmsAct", "name": "Arms Act, 1959", "url_path": "/handle/123456789/1398"},
            {"id": "ITAct", "name": "Information Technology Act, 2000", "url_path": "/handle/123456789/1999"},
        ]

        for act_config in act_configs:
            state_key = f"indiacode:{act_config['id']}"
            if self._state.get(state_key):
                continue

            logger.info(f"Fetching: {act_config['name']}")
            url = f"{self.BASE_URL}{act_config['url_path']}"

            response = self.fetch_page(url)
            if not response:
                continue

            soup = BeautifulSoup(response.text, "lxml")
            content = soup.select_one(".act-content") or soup.select_one("#content") or soup.select_one("body")

            if content:
                doc = ScrapedDocument(
                    source=SourceName.INDIA_CODE,
                    source_url=url,
                    document_type=DocumentType.BARE_ACT,
                    title=act_config["name"],
                    content=content.get_text(separator="\n", strip=True),
                    html_content=str(content),
                    language="en",
                    metadata={
                        "act_id": act_config["id"],
                        "act_name": act_config["name"],
                    },
                )
                yield doc

            self._state[state_key] = True
            self._save_state()


def create_india_code_source(output_dir: str = "data/sources/indiacode") -> IndiaCodeDataSource:
    config = DataSourceConfig(
        base_url="https://www.indiacode.nic.in",
        output_dir=output_dir,
        delay_seconds=2.0,
        max_concurrent=1,
        max_retries=3,
        timeout=30,
    )
    return IndiaCodeDataSource(config)
