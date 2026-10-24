# Local claim reader: GPU run

EasyOCR load 18.5s (once). Scored on demo-001.png, demo-002.png, demo-003.png (56 fields); ex_s* are unscored stress samples.

| model | fields right (scored) | claims invented | failed reads | mean OCR s | mean model s | peak VRAM MiB |
|---|---|---|---|---|---|---|
| qwen2.5:3b | 49/56 | 0 | 0 | 1.2 | 3.0 | 7872 |
| gemma3:4b | 56/56 | 0 | 0 | 1.0 | 3.3 | 7872 |

## Per field

| sample | claim | field | expected | qwen2.5:3b | gemma3:4b |
|---|---|---|---|---|---|
| demo-001.png | holding:Reliance Industries | instrument_name | Reliance Industries | ok Reliance Industries | ok Reliance Industries |
| demo-001.png | holding:Reliance Industries | isin | None | ok None | ok None |
| demo-001.png | holding:Reliance Industries | quantity | 5000 | ok 5000 | ok 5000 |
| demo-001.png | holding:Reliance Industries | value_inr | 15200000.0 | ok 15200000.0 | ok 15200000.0 |
| demo-001.png | holding:Tata Consultancy Services | instrument_name | Tata Consultancy Services | ok Tata Consultancy Services | ok Tata Consultancy Services |
| demo-001.png | holding:Tata Consultancy Services | isin | None | ok None | ok None |
| demo-001.png | holding:Tata Consultancy Services | quantity | 3000 | ok 3000 | ok 3000 |
| demo-001.png | holding:Tata Consultancy Services | value_inr | 12600000.0 | ok 12600000.0 | ok 12600000.0 |
| demo-001.png | holding:Infosys | instrument_name | Infosys | ok Infosys | ok Infosys |
| demo-001.png | holding:Infosys | isin | None | ok None | ok None |
| demo-001.png | holding:Infosys | quantity | 8000 | ok 8000 | ok 8000 |
| demo-001.png | holding:Infosys | value_inr | 12000000.0 | ok 12000000.0 | ok 12000000.0 |
| demo-001.png | broker:Zyphra Stock Club | name | Zyphra Stock Club | ok Zyphra Stock Club | ok Zyphra Stock Club |
| demo-001.png | broker:Zyphra Stock Club | sebi_reg_no | None | ok None | ok None |
| demo-001.png | broker:Zyphra Stock Club | claims_registered | True | ok True | ok True |
| demo-001.png | payee:zyphrastock.invest@mockupi | upi_id | zyphrastock.invest@mockupi | WRONG (claim missing) | ok zyphrastock.invest@mockupi |
| demo-001.png | payee:zyphrastock.invest@mockupi | account_no_last4 | None | WRONG (claim missing) | ok None |
| demo-001.png | payee:zyphrastock.invest@mockupi | ifsc | None | WRONG (claim missing) | ok None |
| demo-001.png | payee:zyphrastock.invest@mockupi | described_as | broker | WRONG (claim missing) | ok broker |
| demo-001.png | portfolio | total_inr | 39800000.0 | WRONG None | ok 39800000.0 |
| demo-002.png | holding:Nahar Spinning Mills Limited | instrument_name | Nahar Spinning Mills Limited | ok Nahar Spinning Mills Limited | ok Nahar Spinning Mills Limited |
| demo-002.png | holding:Nahar Spinning Mills Limited | isin | None | ok None | ok None |
| demo-002.png | holding:Nahar Spinning Mills Limited | quantity | 3006 | ok 3006 | ok 3006 |
| demo-002.png | holding:Nahar Spinning Mills Limited | value_inr | 1140506.0 | ok 1140506.0 | ok 1140506.0 |
| demo-002.png | holding:Cravatex Limited | instrument_name | Cravatex Limited | ok Cravatex Limited | ok Cravatex Limited |
| demo-002.png | holding:Cravatex Limited | isin | None | ok None | ok None |
| demo-002.png | holding:Cravatex Limited | quantity | 3242 | ok 3242 | ok 3242 |
| demo-002.png | holding:Cravatex Limited | value_inr | 244447.0 | ok 244447.0 | ok 244447.0 |
| demo-002.png | holding:Sintercom India Limited | instrument_name | Sintercom India Limited | ok Sintercom India Limited | ok Sintercom India Limited |
| demo-002.png | holding:Sintercom India Limited | isin | None | ok None | ok None |
| demo-002.png | holding:Sintercom India Limited | quantity | 4405 | ok 4405 | ok 4405 |
| demo-002.png | holding:Sintercom India Limited | value_inr | 2254831.0 | ok 2254831.0 | ok 2254831.0 |
| demo-002.png | holding:BF Utilities Limited | instrument_name | BF Utilities Limited | ok BF Utilities Limited | ok BF Utilities Limited |
| demo-002.png | holding:BF Utilities Limited | isin | None | ok None | ok None |
| demo-002.png | holding:BF Utilities Limited | quantity | 3029 | ok 3029 | ok 3029 |
| demo-002.png | holding:BF Utilities Limited | value_inr | 8171818.0 | ok 8171818.0 | ok 8171818.0 |
| demo-002.png | broker:ZERODHA BROKING LIMITED | name | ZERODHA BROKING LIMITED | ok ZERODHA BROKING LIMITED | ok ZERODHA BROKING LIMITED |
| demo-002.png | broker:ZERODHA BROKING LIMITED | sebi_reg_no | None | ok None | ok None |
| demo-002.png | broker:ZERODHA BROKING LIMITED | claims_registered | True | ok True | ok True |
| demo-002.png | portfolio | total_inr | 11811602.0 | WRONG None | ok 11811602.0 |
| demo-003.png | holding:Century Extrusions Limited | instrument_name | Century Extrusions Limited | ok Century Extrusions Limited | ok Century Extrusions Limited |
| demo-003.png | holding:Century Extrusions Limited | isin | None | ok None | ok None |
| demo-003.png | holding:Century Extrusions Limited | quantity | 3266 | ok 3266 | ok 3266 |
| demo-003.png | holding:Century Extrusions Limited | value_inr | 10188302.0 | ok 10188302.0 | ok 10188302.0 |
| demo-003.png | holding:Trent Limited | instrument_name | Trent Limited | ok Trent Limited | ok Trent Limited |
| demo-003.png | holding:Trent Limited | isin | None | ok None | ok None |
| demo-003.png | holding:Trent Limited | quantity | 2701 | ok 2701 | ok 2701 |
| demo-003.png | holding:Trent Limited | value_inr | 20898774.0 | ok 20898774.0 | ok 20898774.0 |
| demo-003.png | holding:Shilpa Medicare Limited | instrument_name | Shilpa Medicare Limited | ok Shilpa Medicare Limited | ok Shilpa Medicare Limited |
| demo-003.png | holding:Shilpa Medicare Limited | isin | None | ok None | ok None |
| demo-003.png | holding:Shilpa Medicare Limited | quantity | 4381 | ok 4381 | ok 4381 |
| demo-003.png | holding:Shilpa Medicare Limited | value_inr | 18429950.0 | ok 18429950.0 | ok 18429950.0 |
| demo-003.png | broker:ZERODHA BROKING LIMITED | name | ZERODHA BROKING LIMITED | ok ZERODHA BROKING LIMITED | ok ZERODHA BROKING LIMITED |
| demo-003.png | broker:ZERODHA BROKING LIMITED | sebi_reg_no | None | ok None | ok None |
| demo-003.png | broker:ZERODHA BROKING LIMITED | claims_registered | True | ok True | ok True |
| demo-003.png | portfolio | total_inr | 49517026.0 | WRONG None | ok 49517026.0 |
| ex_s1.png | holding:Infosys | instrument_name | Infosys | WRONG Inicsys | WRONG (claim missing) |
| ex_s1.png | holding:Infosys | isin | INE009A01021 | WRONG None | WRONG (claim missing) |
| ex_s1.png | holding:Infosys | quantity | 8000 | WRONG 12 | WRONG (claim missing) |
| ex_s1.png | holding:Infosys | value_inr | None | ok None | WRONG (claim missing) |
| ex_s1.png | portfolio | total_inr | 120000 | WRONG None | WRONG None |
| ex_s2.png | holding:Reliance Industries | instrument_name | Reliance Industries | WRONG Faliance Industries | WRONG Faliance Industries |
| ex_s2.png | holding:Reliance Industries | isin | INE002A01018 | WRONG None | WRONG INONEIINNONE |
| ex_s2.png | holding:Reliance Industries | quantity | 5000 | WRONG None | WRONG None |
| ex_s2.png | holding:Reliance Industries | value_inr | None | ok None | ok None |
| ex_s2.png | portfolio | total_inr | None | ok None | ok None |
