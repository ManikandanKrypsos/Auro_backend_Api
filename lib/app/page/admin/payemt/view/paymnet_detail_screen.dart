import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/primary_button.dart';
import '../../../../widgets/secondary_button.dart';

class InvoiceDetailScreen extends StatelessWidget {
  const InvoiceDetailScreen({super.key});

  // ── Static Data ───────────────────────────────────────
  static const _patient = 'Margot Fontaine';
  static const _invoiceId = '#AURA-2024-8842';
  static const _therapist = 'Dr. Julianne Moore';
  static const _date = 'October 24, 2024';
  static const _serviceName = 'Signature Gold Facial';
  static const _serviceCategory = 'Dermatology';
  static const _serviceDuration = '90 Minutes';
  static const _servicePrice = 420.00;
  static const _taxRate = 0.07;
  static const _paymentMethod = 'VISA •••• 4242';
  static const _status = 'PENDING';

  double get _subtotal => _servicePrice;
  double get _tax => _subtotal * _taxRate;
  double get _total => _subtotal + _tax;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: _buildAppBar(context),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 40),
        child: Column(
          children: [
            // ── Invoice Card ──
            _buildInvoiceCard(),
            const SizedBox(height: 28),

            // ── Primary Action ──
            PrimaryButton(label: 'MARK AS PAID', onTap: () {}),
            const SizedBox(height: 12),

            // ── Secondary Action ──
            SecondaryButton(
              title: 'GENERATE PDF INVOICE',
              onTap: () {},
            ),
            const SizedBox(height: 20),

            // ── Edit Link ──
            GestureDetector(
              onTap: () {},
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.edit_outlined,
                    size: 13,
                    color: ColorResources.liteTextColor.withOpacity(0.5),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    'EDIT PAYMENT DETAILS',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.5),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── AppBar ────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: ColorResources.blackColor,
      elevation: 0,
      leading: GestureDetector(
        onTap: () => Navigator.pop(context),
        child: const Icon(Icons.arrow_back_ios,
            color: ColorResources.whiteColor, size: 18),
      ),
      title: const Text(
        'INVOICE DETAIL',
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor,
          fontSize: 13,
          fontWeight: FontWeight.w600,
          letterSpacing: 3.5,
        ),
      ),
      centerTitle: true,
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 16),
          child: CircleAvatar(
            radius: 18,
            backgroundColor: ColorResources.cardColor,
            child: Icon(Icons.person_outline,
                color: ColorResources.liteTextColor, size: 18),
          ),
        ),
      ],
    );
  }

  // ── Invoice Card ──────────────────────────────────────
  Widget _buildInvoiceCard() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header Info ──
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildHeaderField(label: 'PATIENT', value: _patient),
                    _buildHeaderField(
                        label: 'INVOICE ID',
                        value: _invoiceId,
                        align: CrossAxisAlignment.end),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildHeaderField(
                        label: 'LEAD THERAPIST', value: _therapist),
                    _buildHeaderField(
                        label: 'DATE',
                        value: _date,
                        align: CrossAxisAlignment.end),
                  ],
                ),
              ],
            ),
          ),

          _buildDivider(),

          // ── Service Details ──
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SERVICE DETAILS',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2.5,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _serviceName,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 17,
                            fontWeight: FontWeight.w500,
                            letterSpacing: 0.3,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$_serviceCategory • $_serviceDuration',
                          style: AppTextStyles.bodyItalic.copyWith(
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    Text(
                      '€${_servicePrice.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          _buildDivider(),

          // ── Totals ──
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
            child: Column(
              children: [
                _buildTotalRow(
                  label: 'Subtotal',
                  value: '€${_subtotal.toStringAsFixed(2)}',
                ),
                const SizedBox(height: 10),
                _buildTotalRow(
                  label:
                      'Tax / VAT (${(_taxRate * 100).toInt()}%)',
                  value: '€${_tax.toStringAsFixed(2)}',
                ),
                const SizedBox(height: 14),
                _buildDivider(),
                const SizedBox(height: 14),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'TOTAL AMOUNT',
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 2.5,
                      ),
                    ),
                    Text(
                      '€${_total.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 24,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),

          _buildDivider(),

          // ── Payment Method + Status ──
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'PAYMENT METHOD',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor.withOpacity(0.6),
                        fontSize: 9,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(
                          Icons.credit_card_outlined,
                          color: ColorResources.liteTextColor,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _paymentMethod,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'STATUS',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor.withOpacity(0.6),
                        fontSize: 9,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildStatusBadge(_status),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Header Field ──────────────────────────────────────
  Widget _buildHeaderField({
    required String label,
    required String value,
    CrossAxisAlignment align = CrossAxisAlignment.start,
  }) {
    return Column(
      crossAxisAlignment: align,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor.withOpacity(0.6),
            fontSize: 9,
            fontWeight: FontWeight.w600,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          value,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 15,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }

  // ── Total Row ─────────────────────────────────────────
  Widget _buildTotalRow({required String label, required String value}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor.withOpacity(0.7),
            fontSize: 13,
            letterSpacing: 0.3,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 13,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }

  // ── Status Badge ──────────────────────────────────────
  Widget _buildStatusBadge(String status) {
    final Color color = status == 'PAID'
        ? ColorResources.positiveColor
        : status == 'PENDING'
            ? ColorResources.primaryColor
            : ColorResources.negativeColor;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.4), width: 0.8),
      ),
      child: Text(
        status,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.5,
        ),
      ),
    );
  }

  // ── Divider ───────────────────────────────────────────
  Widget _buildDivider() {
    return Divider(
      color: ColorResources.borderColor,
      thickness: 0.5,
      height: 1,
    );
  }
}