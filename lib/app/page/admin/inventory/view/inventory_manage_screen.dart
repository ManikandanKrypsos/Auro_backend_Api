import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../widgets/app_drop_down.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/custom_textform_lables.dart';
import '../../../../widgets/custom_textformfeild.dart';
import '../../../../widgets/primary_button.dart';

class InventoryManageScreen extends StatefulWidget {
  final bool isEdit;
  const InventoryManageScreen({super.key,  this.isEdit=false});

  @override
  State<InventoryManageScreen> createState() => _InventoryManageScreenState();
}

class _InventoryManageScreenState extends State<InventoryManageScreen> {
  // ── Controllers ──────────────────────────────────────
  final _itemNameController = TextEditingController();
  final _initialStockController = TextEditingController(text: '0');
  final _minStockController = TextEditingController();
  final _supplierNameController = TextEditingController();
  final _costPerUnitController = TextEditingController(text: '0.00');

  // ── Dropdown Values ───────────────────────────────────
  String? _selectedCategory;
  String? _selectedUnit;

  static const _categories = ['Consumable', 'Equipment'];
  static const _units = ['ml', 'pcs', 'units', 'kg', 'g', 'L'];

  @override
  void dispose() {
    _itemNameController.dispose();
    _initialStockController.dispose();
    _minStockController.dispose();
    _supplierNameController.dispose();
    _costPerUnitController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar:  CustomAppBar(title:widget. isEdit?'UPDATE ITEM':'ADD ITEM'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Basic Information ──────────────────────
            _buildSection(
              label: 'BASIC INFORMATION',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Item Name'),
                  CustomTextField(
                    controller: _itemNameController,
                    hint: 'e.g. Juvederm Voluma',
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const CustomLabel(text: 'Category'),
                            AppDropdown(
                              hint: 'Category',
                              value: _selectedCategory,
                              items: _categories,
                              onChanged: (v) =>
                                  setState(() => _selectedCategory = v),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const CustomLabel(text: 'Unit'),
                            AppDropdown(
                              hint: 'Unit',
                              value: _selectedUnit,
                              items: _units,
                              onChanged: (v) =>
                                  setState(() => _selectedUnit = v),
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

            // ── Stock Control ──────────────────────────
            _buildSection(
              label: 'STOCK CONTROL',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Initial Stock Quantity'),
                  CustomTextField(
                    controller: _initialStockController,
                    hint: '0',
                    keyboardType: TextInputType.number,
                  ),
                  const SizedBox(height: 16),
                  const CustomLabel(text: 'Minimum Stock Alert'),
                  CustomTextField(
                    controller: _minStockController,
                    hint: 'Notify when below...',
                    keyboardType: TextInputType.number,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // ── Supplier Information ───────────────────
            _buildSection(
              label: 'SUPPLIER INFORMATION',
              isOptional: true,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'Supplier Name'),
                  CustomTextField(
                    controller: _supplierNameController,
                    hint: 'Enter supplier name',
                  ),const SizedBox(height: 16),
                    const CustomLabel(text: 'Supplier Phone Number'),
                  CustomTextField(
                    controller: _supplierNameController,
                    hint: 'Enter Phone Number ',
                  ),
                  const SizedBox(height: 16),
                  const CustomLabel(text: 'Cost per Unit (\$)'),
                  CustomTextField(
                    controller: _costPerUnitController,
                    hint: '0.00',
                    keyboardType: const TextInputType.numberWithOptions(
                        decimal: true),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),

      // ── Save Button ────────────────────────────────────
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        child: PrimaryButton(
          label:widget.isEdit?'UPDATE ITEM': 'SAVE ITEM',
          onTap: () {},
        ),
      ),
    );
  }

  // ── Section Card Builder ─────────────────────────────
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
          // ── Section Header ──
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