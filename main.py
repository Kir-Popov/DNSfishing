import time
import homoglyphs as hg
import gevent
from gevent import socket
import json


class DnsFishing:

    def __init__(self, keywords):
        self.__keywords = keywords
        self._possible_domains = []
        self.existing_domains = []
        self._DOMAIN_ZONES = ['com', 'ru', 'net', 'org', 'info', 'cn', 'es', 'top', 'au', 'pl', 'it', 'uk', 'tk', 'ml',
                              'ga', 'cf', 'us', 'xyz', 'top', 'site', 'win', 'bid']

    def __adding_domain_zone(self, domain):
        new_domains = []
        for zone in self._DOMAIN_ZONES:
            new_domain = domain + '.' + zone
            new_domains.append(new_domain)
        return new_domains

    def __adding_end_symbol(self, domain):
        possible_symbols = 'qwertyuiopasdfghjklzxcvbnm1234567890'
        new_domains = []
        for char in possible_symbols:
            new_domain = domain + char
            new_domains.extend(self.__adding_domain_zone(new_domain))
        self._possible_domains.extend(new_domains)

    def __homoglyphs_domains(self, domain):
        homoglyphs = hg.Homoglyphs(languages={'en'}, strategy=hg.STRATEGY_LOAD)
        possible_domains = homoglyphs.to_ascii(domain)
        new_domains = []
        for new_domain in possible_domains:
            new_domains.extend(self.__adding_domain_zone(new_domain))
        self._possible_domains.extend(new_domains)

    def __sub_domains(self, domain):
        if len(domain) == 1:
            return

        new_domains = []
        for i in range(1, len(domain)):
            new_domain = domain[:i] + '.' + domain[i:]
            new_domains.extend(self.__adding_domain_zone(new_domain))
        self._possible_domains.extend(new_domains)

    def __delete_symbol_domains(self, domain):
        if len(domain) == 1:
            return

        new_domains = []
        for i in range(len(domain)):
            new_domain = domain[:i] + domain[i + 1:]
            new_domains.extend(self.__adding_domain_zone(new_domain))
        self._possible_domains.extend(new_domains)

    @staticmethod
    def __check_ip(domain):
        try:
            ip = socket.gethostbyname(domain)
            print(domain, ip)
            return domain, ip
        except Exception as e:
            print(domain, e)
            return None

    def work(self):
        for keyword in self.__keywords:      # Generating possible domains
            self.__adding_end_symbol(keyword)
            self.__sub_domains(keyword)
            self.__delete_symbol_domains(keyword)
            self.__homoglyphs_domains(keyword)

        start_time = time.time()
        print(f"Generated {len(self._possible_domains)} domains")

        jobs = []
        for domain in self._possible_domains:
            jobs.append(gevent.spawn(self.__check_ip, domain))
        _ = gevent.joinall(jobs)

        # Clean jobs from None
        for job in jobs:
            if job.value is not None:
                self.existing_domains.append(job.value)

        print("\n%s seconds -" % (time.time() - start_time), 'Work time')
        print("%s seconds -" % ((time.time() - start_time) / len(self._possible_domains)), 'Average time per domain')
        return self.existing_domains


def main():
    print("Введите ключевые слова и нажмите Enter")
    keywords = input().split()
    print(keywords)
    fish = DnsFishing(keywords)
    correct_domains = fish.work()
    result = []
    for domain in correct_domains:
        result.append(
            {
                "Domain": domain[0],
                "IP_address": domain[1]
            }
        )
    with open('domains.json', 'w') as f:
        json.dump(result, f, sort_keys=False, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
