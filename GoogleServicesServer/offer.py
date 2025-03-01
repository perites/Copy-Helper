import google_services
import logging

parent_folder_id = '1-WFEkKNjVjaJDNt2XKBeJhpIQUviBVim'  # get from db

priority_products_table_id = '1e40khWM1dKTje_vZi4K4fL-RA8-D6jhp2wmZSXurQH0'  # get from db


class OfferGoogleDriveHelper(google_services.GoogleDrive):
    def __init__(self, credentials):
        super().__init__(credentials)

    def get_copy_files(self, lift_folder):
        lift_folder_files = self.get_files_from_folder(lift_folder['id'])

        lift_file = None
        mjml_found = False

        sl_file = None

        for file in lift_folder_files:
            if not mjml_found:
                if (file['name'].lower().endswith('.html')) and ('mjml' in file['name'].lower()) and (
                        'SL' not in file['name']):
                    lift_file = file
                    mjml_found = True
                    logging.debug(f"Found copy file (mjml): {lift_file['name']}")

                elif (not lift_file) and (file['name'].lower().endswith('.html')) and ('SL' not in file['name']):
                    lift_file = file

            if not sl_file:
                if 'sl' in file['name'].lower():
                    sl_file = file
                    logging.debug(f"Found SL file: {sl_file['name']}")

            if mjml_found and sl_file:
                break

        return lift_file, sl_file

    def get_offer_general_folder(self, offer_name):
        for partner_folder in self.get_folders_of_folder(parent_folder_id):

            partner_folder_id = partner_folder['id']
            offer_general_folder = google_services.GoogleDrive.get_folder_by_name(offer_name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        logging.warning(f'No Partners with offer {offer_name} was found in GoogleDrive')

    def get_offer_folder_id(self, offer_name, offer_general_folder):
        offer_folder_id = self.get_folder_by_name('HTML+SL', offer_general_folder, strict=False)
        if not offer_folder_id:
            logging.debug(
                f'Folder "HTML+SL" was not found for offer {offer_name}. Folder id where searching: {offer_general_folder}')
            return

        return offer_folder_id['id']


class OfferGoogleSheetHelper(google_services.GoogleSheets):
    def __init__(self, credentials):
        super().__init__(credentials)

    def get_priority_offer_coordinates(self, offer_name, pages_to_search):
        for page in pages_to_search:
            priority_product_index = self.get_table_index_of_value(
                priority_products_table_id, offer_name, f'{page}!A:A', is_row=False)

            if priority_product_index:
                return priority_product_index, page

        return False, False
