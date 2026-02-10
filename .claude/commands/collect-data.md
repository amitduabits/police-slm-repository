Run the data collection pipeline to fetch real, verified legal data from official sources.

Execute in this order:

1. **India Code (Bare Acts + Section Mappings)** - FIRST, this is foundational
   Run: `python -m src.cli collect run --source india_code`
   Then: `python -m src.cli collect save-mappings`
   This downloads IPC, BNS, CrPC, BNSS, IEA, BSA, NDPS, POCSO, Arms Act, IT Act
   and generates configs/ipc_to_bns_mapping.json, configs/crpc_to_bnss_mapping.json, configs/iea_to_bsa_mapping.json

2. **Indian Kanoon (Court Rulings)** - Largest corpus, most important
   Run: `python -m src.cli collect run --source indian_kanoon --max-results 100`
   This searches 30+ Gujarat-specific criminal law queries and downloads full judgment texts

3. **Gujarat High Court (State HC Judgments)**
   Run: `python -m src.cli collect run --source gujarat_hc --max-results 50`
   Criminal appeals, bail applications from Ahmedabad/Surat/Rajkot benches

4. **Supreme Court (Precedent Rulings)**
   Run: `python -m src.cli collect run --source supreme_court --max-results 30`
   Criminal procedure precedents binding on all Gujarat courts

5. **eCourts India (District Court Data)**
   Run: `python -m src.cli collect run --source ecourts --max-results 50`
   Case data from Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar districts

6. **NCRB (Crime Statistics)**
   Run: `python -m src.cli collect run --source ncrb`
   Crime in India reports for 2020-2022, Gujarat-specific tables

After all sources complete:
- Run: `python -m src.cli collect validate` to check data quality
- Print document counts per source
- Report any sources that failed and suggest fixes
- Print total disk usage of data/sources/

IMPORTANT: All scrapers have rate limiting (2-3 second delays between requests) and resume capability. If interrupted, run the same command again and it will pick up where it left off.
