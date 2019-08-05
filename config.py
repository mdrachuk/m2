from dataclasses import dataclass


@dataclass
class Config:
    name: str
    version: str
    readme_path: str
    author: str
    author_email: str

    @property
    def readme(self):
        with open(self.readme_path, 'r', encoding='utf8') as f:
            return f.read()


config = Config(
    name='serious',
    version='1.0.0.dev10',
    readme_path='README.md',
    author='mdrachuk',
    author_email='misha@drach.uk'
)
