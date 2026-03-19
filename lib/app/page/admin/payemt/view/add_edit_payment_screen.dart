import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/primary_button.dart';
import '../../../../widgets/custom_textformfeild.dart'; 
import '../../../../widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/app_drop_down.dart';



class AddEditPaymentScreen extends StatefulWidget {
  final bool isEdit;
  const AddEditPaymentScreen({super.key, this.isEdit = false});

  @override
  State<AddEditPaymentScreen> createState() => _AddEditPaymentScreenState();
}

class _AddEditPaymentScreenState extends State<AddEditPaymentScreen> {
  // ── Controllers ───────────────────────────────────────
  final _amountController = TextEditingController();
  final _notesController = TextEditingController();

  // ── Dropdown values ───────────────────────────────────
  String? _selectedPatient;
  String? _selectedService;
  String? _selectedPaymentMethod;
  String? _selectedStatus;

  // ── Static options ────────────────────────────────────
  static const _patients = [
    'Eleanor Vance',
    'Julian Sterling',
    'Margot Fontaine',
    'Sebastian Thorne',
    'Isabelle Morel',
    'Damien Cross',
  ];

  static const _services = [
    'Signature Gold Facial',
    'Deep Tissue Therapy',
    'Vitamin C Infusion',
    'Sculptural Face Lift',
    'Hydra-Facial Platinum',
    'Botox — Full Face',
  ];

  static const _paymentMethods = [
    'Cash',
    'VISA',
    'Mastercard',
    'Bank Transfer',
    'Insurance',
  ];

  static const _statuses = ['PAID', 'PENDING', 'CANCELLED'];

  @override
  void dispose() {
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(
        title: widget.isEdit ? 'EDIT PAYMENT' : 'ADD PAYMENT',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Patient Details ───────────────────────
            _buildSection(
              label: 'PATIENT DETAILS',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Patient'),
                  _buildPatientSearch(),
                  const SizedBox(height: 16),
                  const CustomLabel(text: 'Service'),
                  AppDropdown(
                    hint: 'Select service',
                    value: _selectedService,
                    items: _services,
                    onChanged: (v) => setState(() => _selectedService = v),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ── Payment Details ───────────────────────
            _buildSection(
              label: 'PAYMENT DETAILS',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Amount'),
                  CustomTextField(
                    controller: _amountController,
                    hint: '0.00',
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    suffix: Padding(
                      padding: const EdgeInsets.only(right: 14),
                      child: Text(
                        '\$',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.primaryColor,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const CustomLabel(text: 'Payment Method'),
                            AppDropdown(
                              hint: 'Select method',
                              value: _selectedPaymentMethod,
                              items: _paymentMethods,
                              onChanged: (v) => setState(
                                  () => _selectedPaymentMethod = v),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const CustomLabel(text: 'Status'),
                            AppDropdown(
                              hint: 'Select status',
                              value: _selectedStatus,
                              items: _statuses,
                              onChanged: (v) =>
                                  setState(() => _selectedStatus = v),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ── Notes ─────────────────────────────────
            _buildSection(
              label: 'NOTES',
              isOptional: true,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Additional Notes'),
                  CustomTextField(
                    controller: _notesController,
                    hint: 'Add any remarks or notes...',
                    maxLine: 4,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),

      // ── Save Button ───────────────────────────────────
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        child: PrimaryButton(
          label: widget.isEdit ? 'UPDATE PAYMENT' : 'SAVE PAYMENT',
          onTap: () {},
        ),
      ),
    );
  }

  // ── Patient Search Field ──────────────────────────────
  Widget _buildPatientSearch() {
    return GestureDetector(
      onTap: () => _showPatientPicker(context),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                _selectedPatient ?? 'Search or select patient',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: _selectedPatient != null
                      ? ColorResources.whiteColor
                      : ColorResources.whiteColor.withOpacity(0.25),
                  fontSize: 15,
                  fontStyle: _selectedPatient != null
                      ? FontStyle.normal
                      : FontStyle.italic,
                ),
              ),
            ),
            Icon(
              Icons.search,
              color: ColorResources.primaryColor.withOpacity(0.7),
              size: 18,
            ),
          ],
        ),
      ),
    );
  }

  // ── Patient Picker Bottom Sheet ───────────────────────
  void _showPatientPicker(BuildContext context) {
    final TextEditingController searchCtrl = TextEditingController();
    List<String> filtered = List.from(_patients);

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111111),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(ctx).viewInsets.bottom,
              ),
              child: Container(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Handle
                    Center(
                      child: Container(
                        width: 36,
                        height: 3,
                        decoration: BoxDecoration(
                          color: ColorResources.borderColor,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Text(
                      'SELECT PATIENT',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2.5,
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Search
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 4),
                      decoration: BoxDecoration(
                        color: ColorResources.cardColor,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                            color: ColorResources.borderColor, width: 0.5),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.search,
                              color:
                                  ColorResources.primaryColor.withOpacity(0.7),
                              size: 16),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextField(
                              controller: searchCtrl,
                              style: const TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.whiteColor,
                                fontSize: 14,
                              ),
                              decoration: InputDecoration(
                                hintText: 'Search patient...',
                                hintStyle: TextStyle(
                                  fontFamily: 'CormorantGaramond',
                                  color: ColorResources.whiteColor
                                      .withOpacity(0.25),
                                  fontSize: 14,
                                ),
                                border: InputBorder.none,
                                isDense: true,
                                contentPadding:
                                    const EdgeInsets.symmetric(vertical: 10),
                              ),
                              cursorColor: ColorResources.primaryColor,
                              onChanged: (v) {
                                setSheetState(() {
                                  filtered = _patients
                                      .where((p) => p
                                          .toLowerCase()
                                          .contains(v.toLowerCase()))
                                      .toList();
                                });
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Patient List
                    ...filtered.map(
                      (p) => GestureDetector(
                        onTap: () {
                          setState(() => _selectedPatient = p);
                          Navigator.pop(ctx);
                        },
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(
                              vertical: 14, horizontal: 4),
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(
                                  color: ColorResources.borderColor,
                                  width: 0.5),
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                p,
                                style: TextStyle(
                                  fontFamily: 'CormorantGaramond',
                                  color: _selectedPatient == p
                                      ? ColorResources.primaryColor
                                      : ColorResources.whiteColor,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              if (_selectedPatient == p)
                                Icon(Icons.check,
                                    color: ColorResources.primaryColor,
                                    size: 16),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  // ── Section Card ──────────────────────────────────────
  Widget _buildSection({
    required String label,
    required Widget child,
    bool isOptional = false,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 2.5,
                ),
              ),
              if (isOptional)
                Text(
                  'Optional',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.5),
                    fontSize: 11,
                    fontStyle: FontStyle.italic,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}