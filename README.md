# waku-interop-tests

Waku e2e and interop framework used to test various implementation of the [Waku v2 protocol](https://rfc.vac.dev/spec/10/).

## Setup and contribute

```shell
git clone git@github.com:waku-org/waku-interop-tests.git
cd waku-interop-tests
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
(optional) Overwrite default vars from src/env_vars.py via cli env vars or by adding a .env file
pytest
```

## CI 

- Test runs via github actions
- [Allure Test Reports](https://waku-org.github.io/waku-interop-tests/3/) are published via github pages


## CI NWAKU job 

To update tests in PRs at nwaku repo following steps shall be done 

 - Make a tag at the desired commit on master with these 2 commands
   - git tag tagname
   - git push origin tagname
 - Navigate to test_PR_image.yml file and modify job "tests" to explicilty use the tag in ref section
  
 ![Screenshot from 2024-12-24 16-24-51](https://github.com/user-attachments/assets/dd3f95bd-fe79-475b-92b7-891d82346382)


## License

Licensed and distributed under either of

- MIT license: [LICENSE-MIT](https://github.com/waku-org/js-waku/blob/master/LICENSE-MIT) or http://opensource.org/licenses/MIT

or

- Apache License, Version 2.0, ([LICENSE-APACHE-v2](https://github.com/waku-org/js-waku/blob/master/LICENSE-APACHE-v2) or http://www.apache.org/licenses/LICENSE-2.0)

at your option. These files may not be copied, modified, or distributed except according to those terms.
