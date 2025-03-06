class DomainGoogleSheetsHelper:
    @classmethod
    def get_copies(cls, name, page, broadcast_date):

        broadcast_id = settings.GeneralSettings.broadcast_id

        domain_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, name, f'{page}!1:1')

        if not domain_index:
            logging.warning(f'Could not find domain {name} in Broadcast')
            return

        date_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, broadcast_date, f'{page}!A:A',
                                                                           False)
        if not domain_index:
            logging.warning(f'Could not find date {broadcast_date} in Broadcast')
            return

        date_row = date_index + 1
        copies_range = f'{page}!{date_row}:{date_row}'
        copies_for_date = google_services.GoogleSheets.get_data_from_range(broadcast_id, copies_range)
        copies_for_domain = copies_for_date[0][domain_index]
        if not copies_for_domain:
            logging.warning(f'Could not find copies in range {copies_range} in Broadcast')
            return

        return copies_for_domain.strip().split(' ')
