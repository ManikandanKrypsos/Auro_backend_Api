import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/custom_appbar.dart';

class ProductUsageScreen extends StatefulWidget {
  const ProductUsageScreen({super.key});

  @override
  State<ProductUsageScreen> createState() => _ProductUsageScreenState();
}

class _ProductUsageScreenState extends State<ProductUsageScreen> {
  int _selectedTab = 0;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  static const _tabs = ['TODAY', 'THIS WEEK', 'ALL'];

  // ── Static usage data ─────────────────────────────────
  static const List<Map<String, dynamic>> _usageData = [
    {
      'product': 'Gentle Cleanser',
      'quantity': 5,
      'unit': 'ml',
  
      'date': 'Oct 24, 2024',
      'time': '11:45 AM',
      'session': 2,
      'totalSessions': 5,
      'notes': 'Applied before serum step.',
      'period': 'today',
    },
    {
      'product': 'Hyaluronic Acid Serum',
      'quantity': 3,
      'unit': 'ml',
    
      'date': 'Oct 24, 2024',
      'time': '11:45 AM',
      'session': 2,
      'totalSessions': 5,
      'notes': '',
      'period': 'today',
    },
    {
      'product': 'SPF 50 Broad Spectrum',
      'quantity': 2,
      'unit': 'ml',

      'date': 'Oct 24, 2024',
      'time': '03:45 PM',
      'session': 1,
      'totalSessions': 1,
      'notes': 'Post-treatment sun protection.',
      'period': 'today',
    },
    {
      'product': 'Calming Rose Toner',
      'quantity': 4,
      'unit': 'ml',

      'date': 'Oct 23, 2024',
      'time': '09:00 AM',
      'session': null,
      'totalSessions': null,
      'notes': '',
      'period': 'week',
    },
    {
      'product': '24K Gold Facial Serum',
      'quantity': 1,
      'unit': 'pcs',

      'date': 'Oct 23, 2024',
      'time': '09:00 AM',
      'session': null,
      'totalSessions': null,
      'notes': 'Full application. Patient responded well.',
      'period': 'week',
    },
    {
      'product': 'Niacinamide Essence',
      'quantity': 6,
      'unit': 'ml',
   
      'date': 'Oct 22, 2024',
      'time': '02:30 PM',
      'session': null,
      'totalSessions': null,
      'notes': '',
      'period': 'week',
    },
    {
      'product': 'Collagen Boost Mask',
      'quantity': 1,
      'unit': 'pcs',

      'date': 'Oct 18, 2024',
      'time': '10:30 AM',
      'session': null,
      'totalSessions': null,
      'notes': '',
      'period': 'all',
    },
    {
      'product': 'Peptide Eye Cream',
      'quantity': 2,
      'unit': 'g',
      
      'date': 'Oct 15, 2024',
      'time': '09:30 AM',
      'session': null,
      'totalSessions': null,
      'notes': 'Sensitive area, applied lightly.',
      'period': 'all',
    },
  ];

  // ── Filtered ──────────────────────────────────────────
  List<Map<String, dynamic>> get _filtered {
    List<Map<String, dynamic>> items;
    switch (_selectedTab) {
      case 0:
        items = _usageData.where((i) => i['period'] == 'today').toList();
        break;
      case 1:
        items = _usageData
            .where((i) => i['period'] == 'today' || i['period'] == 'week')
            .toList();
        break;
      default:
        items = _usageData;
    }
    if (_searchQuery.isNotEmpty) {
      final q = _searchQuery.toLowerCase();
      items = items
          .where((i) =>
              (i['product'] as String).toLowerCase().contains(q) ||
              (i['patient'] as String).toLowerCase().contains(q) ||
              (i['service'] as String).toLowerCase().contains(q))
          .toList();
    }
    return items;
  }

  // ── Summary stats ─────────────────────────────────────
  int get _totalItems => _filtered.length;
  int get _totalPatients =>
      _filtered.map((i) => i['patient']).toSet().length;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'PRODUCT USAGE'),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),

          // ── Search ──
          AppSearchBar(
            hintText: 'Search product, patient or service...',
            controller: _searchController,
            onChanged: (v) => setState(() => _searchQuery = v),
          ),
          const SizedBox(height: 16),

          // ── Tabs ──
          _buildTabRow(),
          const SizedBox(height: 16),

      

          // ── List ──
          Expanded(
            child: _filtered.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
                    itemCount: _filtered.length,
                    itemBuilder: (_, i) => _buildUsageCard(_filtered[i]),
                  ),
          ),
        ],
      ),
    );
  }

  // ── Tab Row ───────────────────────────────────────────
  Widget _buildTabRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_tabs.length, (i) {
          final isSelected = _selectedTab == i;
          return GestureDetector(
            onTap: () => setState(() => _selectedTab = i),
            child: Padding(
              padding:
                  EdgeInsets.only(right: i < _tabs.length - 1 ? 36 : 0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _tabs[i],
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isSelected
                          ? ColorResources.primaryColor
                          : ColorResources.liteTextColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    height: 1.5,
                    width: isSelected ? _tabs[i].length * 9.0 : 0,
                    color: ColorResources.primaryColor,
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  // ── Summary Row ───────────────────────────────────────
  Widget _buildSummaryRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          _summaryChip(
              icon: Icons.science_outlined,
              label: '$_totalItems products used'),
          const SizedBox(width: 12),
          _summaryChip(
              icon: Icons.person_outline,
              label: '$_totalPatients patients'),
        ],
      ),
    );
  }

  Widget _summaryChip({required IconData icon, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon,
              size: 13,
              color: ColorResources.primaryColor.withOpacity(0.7)),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.7),
              fontSize: 12,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }

  // ── Usage Card ────────────────────────────────────────
  Widget _buildUsageCard(Map<String, dynamic> item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Row 1: Product + Quantity ──
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  item['product'] as String,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 17,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: ColorResources.primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                      color: ColorResources.primaryColor.withOpacity(0.3),
                      width: 0.5),
                ),
                child: Text(
                  '${item['quantity']} ${item['unit']}',
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
    
          const SizedBox(height: 8),
    
         
    
          // ── Row 3: Date · Time + Session ──
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.access_time_rounded,
                      size: 12,
                      color: ColorResources.liteTextColor.withOpacity(0.4)),
                  const SizedBox(width: 5),
                  Text(
                    '${item['date']}  ·  ${item['time']}',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.5),
                      fontSize: 11,
                      letterSpacing: 0.3,
                    ),
                  ),
                ],
              ),
             
            ],
          ),
        ],
      ),
    );
  }

  // ── Empty State ───────────────────────────────────────
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.science_outlined,
              size: 40,
              color: ColorResources.liteTextColor.withOpacity(0.2)),
          const SizedBox(height: 12),
          Text(
            'NO USAGE RECORDS FOUND',
            style: AppTextStyles.headingSmall.copyWith(
              color: ColorResources.liteTextColor.withOpacity(0.3),
              letterSpacing: 3,
            ),
          ),
        ],
      ),
    );
  }


}

