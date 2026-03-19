import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/primary_button.dart';

class InventoryDetailScreen extends StatelessWidget {
  const InventoryDetailScreen({super.key});

  static const _itemName = '24K Gold Serum';
  static const _itemSubtitle = 'Premium Post-Treatment Glow';
  static const _category = 'CONSUMABLE';
  static const _currentStock = 12;
  static const _unit = 'Units';
  static const _threshold = 10;
  static const _supplier = 'AURA Luxe Lab';
  static const _supplierPhone = '+1 (800) 555-0192';
  static const _unitType = '50ml Bottle';
  static const _lastRestock = 'Oct 12, 2024';

  static const List<Map<String, dynamic>> _movements = [
    {
      'title': 'Added to Inventory',
      'date': 'Oct 12, 2024 • 09:30 AM',
      'change': '+20 Units',
      'positive': true,
    },
    {
      'title': 'Used in Treatment',
      'date': 'Oct 11, 2024 • 02:15 PM',
      'change': '-1 Unit',
      'positive': false,
    },
    {
      'title': 'Used in Treatment',
      'date': 'Oct 10, 2024 • 11:00 AM',
      'change': '-2 Units',
      'positive': false,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title: 'ITEM DETAIL'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // ── Item Title ──
            Text(
              _itemName,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 36,
                fontWeight: FontWeight.w400,
                letterSpacing: 0.5,
                height: 1.1,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _itemSubtitle,
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyItalic,
            ),
            const SizedBox(height: 24),

            // ── Stock Card ──
            _buildStockCard(),
            const SizedBox(height: 20),

            // ── Info Grid ──
            _buildInfoGrid(),
            const SizedBox(height: 28),

            // ── Stock Movement ──
            _buildStockMovementSection(),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        child: PrimaryButton(
          label: '+ ORDER MORE',
          onTap: () {
            Get.toNamed(PageRoutes.inventoryManageScreen, arguments: true);
          },
        ),
      ),
    );
  }



  // ── Stock Card ────────────────────────────────────────
  Widget _buildStockCard() {
    final double stockPercent = (_currentStock / (_threshold * 3)).clamp(
      0.0,
      1.0,
    );

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'CURRENT STOCK',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 2.5,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Stock number
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    '$_currentStock',
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 52,
                      fontWeight: FontWeight.w500,
                      height: 1,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    _unit,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor,
                      fontSize: 16,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              ),
              // Threshold
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text(
                    'THRESHOLD',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor,
                      fontSize: 9,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(
                        Icons.arrow_upward_rounded,
                        color: ColorResources.primaryColor,
                        size: 14,
                      ),
                      Text(
                        ' $_threshold Min',
                        style: const TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.primaryColor,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: stockPercent,
              minHeight: 3,
              backgroundColor: ColorResources.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(
                ColorResources.primaryColor,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Info Grid ─────────────────────────────────────────
  Widget _buildInfoGrid() {
    final items = [
      {'label': 'SUPPLIER', 'value': _supplier},
      {'label': 'UNIT TYPE', 'value': _unitType},
      {'label': 'SUPPLIER PHONE', 'value': _supplierPhone},
      {'label': 'LAST RESTOCK', 'value': _lastRestock},
      {'label': 'CATEGORY', 'value': _category},
    ];

    // Split into rows of 2
    final rows = <Widget>[];
    for (int i = 0; i < items.length; i += 2) {
      final isLast = i + 1 >= items.length;
      rows.add(
        Row(
          children: [
            Expanded(child: _buildInfoCard(items[i])),
            const SizedBox(width: 12),
            isLast
                ? const Expanded(child: SizedBox())
                : Expanded(child: _buildInfoCard(items[i + 1])),
          ],
        ),
      );
      if (i + 2 < items.length) rows.add(const SizedBox(height: 12));
    }

    return Column(children: rows);
  }

  Widget _buildInfoCard(Map<String, String> data) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            data['label']!,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.6),
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            data['value']!,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 15,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }

  // ── Stock Movement ────────────────────────────────────
  Widget _buildStockMovementSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Stock Movement',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 20,
                fontWeight: FontWeight.w500,
                letterSpacing: 0.3,
              ),
            ),
            GestureDetector(
              onTap: () {},
              child: Text(
                'VIEW ALL',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor.withOpacity(0.85),
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 2,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Movement items
        ..._movements.map((m) => _buildMovementRow(m)),
      ],
    );
  }

  Widget _buildMovementRow(Map<String, dynamic> m) {
    final bool isPositive = m['positive'] as bool;
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Dot indicator
          Column(
            children: [
              Container(
                width: 18,
                height: 18,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 1.5,
                  ),
                  color: ColorResources.cardColor,
                ),
                child: Center(
                  child: Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isPositive
                          ? ColorResources.positiveColor
                          : ColorResources.liteTextColor.withOpacity(0.4),
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(width: 12),
          // Title + Date
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  m['title'] as String,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.2,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  m['date'] as String,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.5),
                    fontSize: 11,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),
          ),
          // Change value
          Text(
            m['change'] as String,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: isPositive
                  ? ColorResources.positiveColor
                  : ColorResources.liteTextColor,
              fontSize: 13,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
