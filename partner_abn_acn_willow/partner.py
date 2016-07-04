from openerp import models, fields

ABN_ACN_VALID_CHARS  = "0123456789"
ABN_ACN_FILLER_CHARS = " -"

class res_partner(models.Model):
    _inherit = 'res.partner'

    abn = fields.Char(string='ABN', size=20, help="Australian Business Number")
    acn = fields.Char(string='ACN', size=20, help="Australian Company Number")
    ird = fields.Char(string='IRD (NZ)', size=20, help="Inland Revenue Department (New Zealand)")

    def strip_abn_acn_ird(self, abn_acn_ird):
        """Remove 'filler' chars from an ABN or ACN.

        Fillers are not valid as chars, but are allowed here to make formatting of the numbers easier, e.g.: 111-111-111-11.

        @return: Passed string with any filler chars removed. Note the return
                 value is not necessarily a valid ABN/ACN. It may still contain
                 invalid chars or have other errors.
        """
        if not abn_acn_ird: # Just in case False is passed
            return ''

        for char in ABN_ACN_FILLER_CHARS:
            abn_acn_ird = abn_acn_ird.replace(char, '')
        return abn_acn_ird


    def validate_abn(self, abn):
        """Validate an ABN value.

        The ABN must be 11 digits, with a valid checksum.

        @returns: Tuple with:
                    [0] - True if ABN is valid, False otherwise.
                    [1] - Error message if [0] is False.
                    [2] - ABN with any separator chars removed.
                          This is only a valid ABN if [0] is True
        """
        res = True
        msg = ''
        stripped_abn = self.strip_abn_acn_ird(abn)
        if stripped_abn:
            for char in stripped_abn:
                if char not in ABN_ACN_VALID_CHARS:
                    res = False
                    msg = "Character '%s' is not valid in an ABN. Valid characters are [%s] and fillers [%s]." % (char, ABN_ACN_VALID_CHARS, ABN_ACN_FILLER_CHARS)
                    break

            if res and (len(stripped_abn) != 11):
                res = False
                msg = "ABN must be 11 digits. Current length is %s." % (len(stripped_abn),)

            if res and stripped_abn.startswith('0'):
                res = False
                msg = "ABN must not have leading zeroes."

            # Do checksum validation.
            # Code from:  http://code.activestate.com/recipes/577692-validate-abns-australian-business-numbers/
            # See also: http://www.ato.gov.au/businesses/content.aspx?doc=/content/13187.htm&pc=001/003/021/002/001&mnu=610&mfp=001/003&st=&cy=1
            if res:
                digits = [int(c) for c in stripped_abn]
                digits[0] -= 1
                weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
                chksum = sum(d*w for d,w in zip(digits, weights)) % 89
                if chksum != 0:
                    res = False
                    msg = "Invalid checksum. Check for keying error."

        return (res, msg, stripped_abn)

    def on_change_abn(self, cr, uid, ids, abn, context={}):
        check_abn = self.validate_abn(abn)
        if not check_abn[0]:
            return {'warning': {'title': 'ABN', 'message': 'ABN is not valid. %s' % check_abn[1]}}
        return {}

    def validate_acn(self, acn):
        """Validate an ACN value.

        The ACN must be 9 digits, ending with a valid check digit.

        @returns: Tuple with:
                    [0] - True if ACN is valid, False otherwise.
                    [1] - Error message if [0] is False.
                    [2] - ACN with any separator chars removed.
                          This is only a valid ACN if [0] is True
        """
        res = True
        msg = ''
        stripped_acn = self.strip_abn_acn_ird(acn)
        if stripped_acn:
            for char in stripped_acn:
                if char not in ABN_ACN_VALID_CHARS:
                    res = False
                    msg = "Character '%s' is not valid in an ACN. Valid characters are [%s] and fillers [%s]." % (char, ABN_ACN_VALID_CHARS, ABN_ACN_FILLER_CHARS)
                    break

            if res and (len(stripped_acn) != 9):
                res = False
                msg = "ACN must be 9 digits. Current length is %s." % (len(stripped_acn),)

            # Do checksum validation.
            # See: http://www.asic.gov.au/asic/asic.nsf/byheadline/Australian+Company+Number+%28ACN%29+Check+Digit
            if res:
                digits = [int(c) for c in stripped_acn[:-1]]
                weights = [8, 7, 6, 5, 4, 3, 2, 1]
                chksum = (10 - (sum(d*w for d,w in zip(digits, weights)) % 10)) % 10
                if chksum != int(stripped_acn[-1]):
                    res = False
                    msg = "Invalid checksum. Check for keying error."

        return (res, msg, stripped_acn)

    def on_change_acn(self, cr, uid, ids, acn, context={}):
        check_acn = self.validate_acn(acn)
        if not check_acn[0]:
            return {'warning': {'title': 'ACN', 'message': 'ACN is not valid. %s' % check_acn[1]}}
        return {}

    def validate_ird(self, ird):
        """Validate an IRD value.

        The IRD must be 8-9 digits, with a valid checksum.

        @returns: Tuple with:
                    [0] - True if IRD is valid, False otherwise.
                    [1] - Error message if [0] is False.
                    [2] - IRD with any separator chars removed.
                          This is only a valid IRD if [0] is True
        """
        res = True
        msg = ''
        stripped_ird = self.strip_abn_acn_ird(ird)
        if stripped_ird:
            for char in stripped_ird:
                if char not in ABN_ACN_VALID_CHARS:
                    res = False
                    msg = "Character '%s' is not valid in an IRD. Valid characters are [%s] and fillers [%s]." % (char, ABN_ACN_VALID_CHARS, ABN_ACN_FILLER_CHARS)
                    break

            if res and len(stripped_ird) == 8:
                stripped_ird = '0' + stripped_ird

            if res and (len(stripped_ird) != 9):
                res = False
                msg = "IRD must be 8 or 9 digits. Current length is %s." % (len(stripped_ird),)

            if res and (stripped_ird < '010000000' or stripped_ird > '150000000'):
                res = False
                msg = 'IRD outside of valid IRD range.'

            # Do checksum validation.
            # See: http://www.ird.govt.nz/resources/3/b/3baac88049703941b60dbf37e0942771/rwt-nrwt-spec-2012.pdf
            if res:
                digits = [int(c) for c in stripped_ird[:-1]]
                weights = [3, 2, 7, 6, 5, 4, 3, 2]
                chksum = (sum(d*w for d,w in zip(digits, weights)) % 11)
                if chksum == 0:
                    chkdig = 0
                elif (11-chksum) < 10:
                    chkdig = 11-chksum
                else:
                    weights = [7, 4, 3, 2, 5, 2, 7, 6]
                    chksum = (sum(d*w for d,w in zip(digits, weights)) % 11)
                    if chksum == 0:
                        chkdig = 0
                    elif (11-chksum) < 10:
                        chkdig = 11-chksum
                    else:
                        res = False
                        msg = 'IRD checksum invalid.'

                if res and int(stripped_ird[-1]) != chkdig:
                    res = False
                    msg = "Invalid checksum. Check for keying error."

        return (res, msg, stripped_ird)

    def on_change_ird(self, cr, uid, ids, ird, context={}):
        check_ird = self.validate_ird(ird)
        if not check_ird[0]:
            return {'warning': {'title': 'IRD', 'message': 'IRD is not valid. %s' % check_ird[1]}}
        return {}
