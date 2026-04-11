import 'package:flutter/material.dart';
import 'app_tab_bar.dart';


class AppTabView extends StatelessWidget {
  final List<String> tabs;
  final List<Widget> children;
  final int selectedTab;
  final ValueChanged<int> onTabChanged;

  const AppTabView({
    super.key,
    required this.tabs,
    required this.children,
    required this.selectedTab,
    required this.onTabChanged,
  }) : assert(tabs.length == children.length,
            'tabs and children must have the same length');

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Scrollable Tab Row ────────────────────────────
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: List.generate(tabs.length, (i) {
              return Padding(
                padding:
                    EdgeInsets.only(right: i < tabs.length - 1 ? 32 : 0),
                child: AppTab(
                  label: tabs[i],
                  index: i,
                  selectedTab: selectedTab,
                  onTap: onTabChanged,
                  activeUnderlineWidth: _labelWidth(tabs[i]),
                ),
              );
            }),
          ),
        ),


        const SizedBox(height: 24),

        // ── Active Content ────────────────────────────────
        children[selectedTab],
      ],
    );
  }

  double _labelWidth(String label) => label.length * 10.0;
}