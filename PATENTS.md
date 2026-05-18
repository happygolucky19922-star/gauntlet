# Patent reference map used in Lucy profiles

This project includes **patent-inspired configuration hooks** (not legal advice and not a claim of patent license).

## Referenced patents

1. US 11,651,211 B2 — "Training of neural network based natural language processing models using dense knowledge distillation"
   - Public link: https://patents.google.com/patent/US11651211B2/en
   - Used to inform: `dense_knowledge_distillation` profile fields in backend runtime metadata and `scripts/lucy.py --use-dkd`.

2. US 12,100,185 B2 — "Non-linear quantization with substitution in neural image compression"
   - Public gazette entry: https://patentsgazette.uspto.gov/week39/OG/html/1526-4/US12100185-20240924.html
   - Used to inform: `nonlinear_quantization` profile fields in backend runtime metadata and `scripts/lucy.py --use-nlq`.

## Scope in codebase

- API endpoint for profile retrieval: `GET /runtime/patent-profiles`.
- Backend profile definitions: `backend/app/optimization/patent_profiles.py`.
- Training utility profile toggles: `scripts/lucy.py`.
