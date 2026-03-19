import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class AppDropdown extends StatelessWidget {
  final String? value;
    final String? hint;
  final List<String> items;
  final ValueChanged<String?> onChanged;

 
  const AppDropdown({
    this.value,
    required this.items,
    required this.onChanged, this.hint,
  });
 
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border:
            Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
         hint: Text(
            hint ?? "Select",
            style:  TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor.withOpacity(0.4),
              fontSize: 15,
            ),
          ),
          value: value,
          isExpanded: true,
          dropdownColor: const Color(0xFF1A1A1A),
          icon: Icon(
            Icons.keyboard_arrow_down,
            color: ColorResources.primaryColor.withOpacity(0.7),
            size: 20,
          ),
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 15,
          ),
          items: items
              .map((i) => DropdownMenuItem(
                    value: i,
                    child: Text(i,
                        style: const TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 15,
                        )),
                  ))
              .toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}