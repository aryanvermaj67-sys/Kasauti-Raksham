# Reader hardening: before and after (dev reader set)

Both runs use the same 24 images in `data/dev_reader/` (made by `scripts/make_dev_reader_set.py`) and the same models.
Before = the committed `local.py` (commit 20a1050); after = the hardened `local.py` (OCR clean-up for Devanagari digits and the rupee sign read as a letter, prompt rules, number validator, UPI format check).
Run with `python -X utf8 scripts/eval_dev_reader.py --model <model> --tag before|after`, then `--compare before after`.
The "before" run is a fresh one on the final images (the earlier "before" run used images that still had a banner).

```
gemma3:4b: before -> after   errors 66 -> 82
  broker.claims_registered           6/7   ->   7/7  
  broker.name                        5/7   ->   7/7  
  broker.sebi_reg_no                 6/7   ->   7/7  
  holding.instrument_name           22/29  ->  20/29 
  holding.isin                      24/29  ->  24/29 
  holding.quantity                  25/29  ->  22/29 
  holding.value_inr                 17/29  ->  19/29 
  language                          17/24  ->  20/24 
  no extra claims                    0/16  ->   0/23 
  payee.account_no_last4             5/5   ->   0/5  
  payee.described_as                 3/5   ->   0/5  
  payee.ifsc                         5/5   ->   0/5  
  payee.upi_id                       0/5   ->   0/5  
  portfolio_total_inr               18/22  ->  18/22 
  total (guard by design)            0/2   ->   1/2  

qwen2.5:3b: before -> after   errors 81 -> 75
  broker.claims_registered           6/7   ->   5/7  
  broker.name                        6/7   ->   6/7  
  broker.sebi_reg_no                 6/7   ->   6/7  
  holding.instrument_name           24/29  ->  23/29 
  holding.isin                      26/29  ->  23/29 
  holding.quantity                  24/29  ->  23/29 
  holding.value_inr                 18/29  ->  20/29 
  language                          10/24  ->   9/24 
  no extra claims                    0/25  ->   0/7  
  payee.account_no_last4             5/5   ->   1/5  
  payee.described_as                 2/5   ->   1/5  
  payee.ifsc                         5/5   ->   1/5  
  payee.upi_id                       0/5   ->   0/5  
  portfolio_total_inr               15/22  ->  17/22 
  total (guard by design)            1/2   ->   1/2
```

## Reading the table

- Better after: broker name, registration number and registered flag (gemma3:4b names 5/7 -> 7/7), language (17/24 -> 20/24), and the total guard (the reader now blanks a total that disagrees with its own lines).
- Worse after: payee fields. When OCR splits a UPI id ("fastreturns club@mockupi" for "fastreturns.club@mockupi"), the hardened reader blanks the id because a guess could name another payee, and a payee with no id, account or IFSC is dropped, so the confirm screen shows no payee claim. The customer can add it by hand. Counting the payee fields, gemma3:4b has more errors after (66 -> 82); qwen2.5:3b has fewer (81 -> 75).
- Holding names and quantities: gemma3:4b slipped by 2-3 fields (instrument_name 22 -> 20, quantity 25 -> 22 of 29); not yet investigated.
- Small sample: 24 images, one run each; model output varies between runs.
