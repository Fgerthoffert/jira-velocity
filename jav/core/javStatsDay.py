import collections
import numpy
import json
import os
import copy


class StatsDay(object):
    """
        The main function of this class goes through all the data points and break it down by day
        It then calculate various metrics for this particular week
        It also look in history to extract trend and evolution over time (such as evolution of the weekly story points 
        average over time)
    """

    def __init__(self, log, config, daily_data):
        self.log = log
        self.config = config
        self.__daily_data = daily_data
        self.__days = collections.OrderedDict()
        self.__daystats_filepath = self.config.config_path + 'stats_days.jsonl'

    @property
    def daily_data(self):
        return self.__daily_data

    @property
    def days(self):
        return self.__days

    @property
    def daystats_filepath(self):
        return self.__daystats_filepath

    def main(self):
        self.log.info('Calculate daily stats throughout the captured period')

        for current_day in self.daily_data:
            day_txt = self.daily_data[current_day]['datetime'].strftime('%Y%m%d')
            self.days[day_txt] = {
                'datetime': self.daily_data[current_day]['datetime']
                , 'daytxt': self.daily_data[current_day]['datetime'].strftime('%A')
                , 'points': self.daily_data[current_day]['points']
                , 'anyday': {'all': {'values': []}}
                , 'sameday': {'all': {'values': []}}
            }
            for week_idx in self.config.get_config_value('rolling_stats'):
                if week_idx not in self.days[day_txt]['sameday']:
                    self.days[day_txt]['anyday'][week_idx] = {'values': []}
                    self.days[day_txt]['sameday'][week_idx] = {'values': []}

            day_found = False
            for scan_day in self.daily_data:
                if day_found:
                    for stats_type in ['anyday', 'sameday']:
                        same_weekday = False
                        if stats_type == 'anyday':
                            self.days[day_txt][stats_type]['all']['values'].append(self.daily_data[scan_day]['points'])
                        elif self.daily_data[current_day]['datetime'].strftime('%A') == self.daily_data[scan_day][
                            'datetime'].strftime('%A') and stats_type == 'sameday':
                            same_weekday = True
                            self.days[day_txt][stats_type]['all']['values'].append(self.daily_data[scan_day]['points'])

                        if self.days[day_txt][stats_type]['all']['values']:
                            self.days[day_txt][stats_type]['all']['avg'] = int(
                                numpy.mean(self.days[day_txt][stats_type]['all']['values']))
                            self.days[day_txt][stats_type]['all']['min'] = min(
                                self.days[day_txt][stats_type]['all']['values'])
                            self.days[day_txt][stats_type]['all']['max'] = max(
                                self.days[day_txt][stats_type]['all']['values'])

                        for week_idx in self.config.get_config_value('rolling_stats'):
                            in_range = False
                            if stats_type == 'anyday' and len(
                                    self.days[day_txt][stats_type]['all']['values']) <= week_idx * 5:
                                in_range = True
                            elif stats_type == 'sameday' and len(
                                    self.days[day_txt][stats_type]['all']['values']) <= week_idx:
                                in_range = True
                            if (stats_type == 'anyday' and in_range is True) or (
                                            in_range is True and same_weekday is True):
                                self.days[day_txt][stats_type][week_idx]['values'].append(
                                    self.daily_data[scan_day]['points'])
                                self.days[day_txt][stats_type][week_idx]['avg'] = int(
                                    numpy.mean(self.days[day_txt][stats_type]['all']['values']))
                                self.days[day_txt][stats_type][week_idx]['min'] = min(
                                    self.days[day_txt][stats_type]['all']['values'])
                                self.days[day_txt][stats_type][week_idx]['max'] = max(
                                    self.days[day_txt][stats_type]['all']['values'])

                if self.daily_data[current_day]['datetime'] == self.daily_data[scan_day]['datetime']:
                    day_found = True

        # Then write content to a JSONL file
        if os.path.isfile(self.daystats_filepath):
            os.remove(self.daystats_filepath)

        # Clear un-necessary array values, and write output to a JSONL file
        for current_day in self.days:
            del self.days[current_day]['anyday']['all']['values']
            del self.days[current_day]['sameday']['all']['values']
            for week_idx in self.config.get_config_value('rolling_stats'):
                for stats_type in ['anyday', 'sameday']:
                    if stats_type in self.days[current_day] and week_idx in self.days[current_day][
                        stats_type] and 'values' in self.days[current_day][stats_type][week_idx]:
                        del self.days[current_day][stats_type][week_idx]['values']

            day_obj = copy.deepcopy(self.days[current_day])
            day_obj['datetime'] = self.days[current_day]['datetime'].isoformat()
            with open(self.daystats_filepath, 'a+') as fileToWrite:
                fileToWrite.write(json.dumps(day_obj) + '\n')

        return self.days