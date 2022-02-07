"""plugins/targets.py

Functions related to handling and checking targets
"""

from .base import Plugin

class Targets(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for plugin in ['Api', 'Db']:
            setattr(self,
                    plugin.lower(),
                    self.registry.get(plugin)(self.state))

    def get_assessments(self):
        """Check which assessments have been completed"""
        res = self.api.request('GET', 'assessments')
        if res.status_code == 200:
            self.db.update_categories(res.json())
            return self.db.categories

    def get_codename_from_slug(self, slug, try_again=True):
        """Return a codename for a target given its slug

        Arguments:
        slug -- Slug of desired target
        """
        targets = self.db.filter_targets(slug=slug)
        if not targets:
            self.get_registered_summary()
            if try_again:
                codename = self.get_codename_from_slug(slug, False)
        else:
            codename = targets[0].codename
        if codename:
            return codename

    def get_current_target(self):
        """Return information about the currenly selected target"""
        res = self.api.request('GET', 'launchpoint')
        if res.status_code == 200:
            j = res.json()
            if j['pending_slug'] != '-1':
                slug = j['pending_slug']
                status = "Connecting"
            else:
                slug = j['slug']
                status = "Connected"
            ret = {
                "slug": slug,
                "codename": self.get_codename_from_slug(slug),
                "status": status
            }
            return ret

    def get_registered_summary(self):
        """Get information on your registered targets"""
        res = self.api.request('GET', 'targets/registered_summary')
        ret = []
        if res.status_code == 200:
            self.db.update_targets(res.json())
            ret = dict()
            for t in res.json():
                ret[t['id']] = t
        return ret

    def get_unregistered(self):
        """Get slugs of all unregistered targets"""
        if not self.db.categories:
            self.get_assessments()
        categories = [c.id for c in self.db.categories]
        query = {
                'filter[primary]': 'unregistered',
                'filter[secondary]': 'all',
                'filter[industry]': 'all',
                'filter[category][]': categories
        }
        res = self.api.request('GET', 'targets', query=query)
        ret = []
        if res.status_code == 200:
            self.db.update_targets(res.json(), is_registered=True)
            for t in res.json():
                ret.append({'codename': t['codename'], 'slug': t['slug']})
        return ret

    def do_register_all(self):
        """Register all unregistered targets"""
        unreg = self.get_unregistered()
        data = '{"ResearcherListing":{"terms":1}}'
        ret = []
        for t in unreg:
            res = self.api.request('POST',
                                   f'targets/{t["slug"]}/signup',
                                   data=data)
            if res.status_code == 200:
                ret.append(t)
        if len(unreg) >= 15:
            ret.extend(self.do_register_all())
        return ret
